from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import clients, logic, models, schemas
from app.auth import CurrentUser, get_current_user
from app.db import get_db

router = APIRouter()


def _balances(db: Session, household_id: int) -> dict[int, int]:
    """Solde = payé + remboursements versés - parts dues - remboursements reçus."""
    balances: dict[int, int] = defaultdict(int)
    expenses = db.scalars(
        select(models.Expense).where(models.Expense.household_id == household_id)
    ).all()
    for expense in expenses:
        balances[expense.paid_by] += expense.amount_cents
        for share in expense.shares:
            balances[share.user_id] -= share.amount_cents
    payments = db.scalars(
        select(models.Payment).where(models.Payment.household_id == household_id)
    ).all()
    for payment in payments:
        balances[payment.from_user] += payment.amount_cents
        balances[payment.to_user] -= payment.amount_cents
    return dict(balances)


@router.post("/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(
    body: schemas.ExpenseIn,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = clients.fetch_meal(body.meal_id, current.token)
    if meal["status"] != "closed":
        raise HTTPException(status_code=409, detail=f"meal is {meal['status']}, not closed")
    existing = db.scalar(select(models.Expense.id).where(models.Expense.meal_id == body.meal_id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="expense already recorded for this meal")

    participants = clients.fetch_participants(body.meal_id, current.token)["participants"]
    if not participants:
        raise HTTPException(status_code=409, detail="meal has no participant")

    shares = logic.compute_shares(
        body.amount_cents, [(p["user_id"], p["portions"]) for p in participants]
    )
    expense = models.Expense(
        household_id=current.household_id,
        meal_id=body.meal_id,
        paid_by=body.paid_by or current.id,
        amount_cents=body.amount_cents,
        description=body.description,
        shares=[models.Share(**share) for share in shares],
    )
    db.add(expense)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="expense already recorded for this meal"
        ) from None
    db.refresh(expense)
    return expense


@router.get("/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = (
        select(models.Expense)
        .where(models.Expense.household_id == current.household_id)
        .order_by(models.Expense.created_at.desc(), models.Expense.id.desc())
    )
    return db.scalars(stmt).all()


@router.get("/balances", response_model=list[schemas.BalanceOut])
def balances(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    result = _balances(db, current.household_id)
    return [
        schemas.BalanceOut(user_id=user_id, balance_cents=balance)
        for user_id, balance in sorted(result.items())
    ]


@router.get("/settlements", response_model=list[schemas.SettlementOut])
def settlements(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return logic.compute_settlements(_balances(db, current.household_id))


@router.post("/payments", response_model=schemas.PaymentOut, status_code=201)
def create_payment(
    body: schemas.PaymentIn,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.to_user == current.id:
        raise HTTPException(status_code=400, detail="cannot pay yourself")
    payment = models.Payment(
        household_id=current.household_id,
        from_user=current.id,
        to_user=body.to_user,
        amount_cents=body.amount_cents,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
