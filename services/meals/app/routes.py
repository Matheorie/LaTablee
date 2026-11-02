import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.schemas import as_utc

router = APIRouter()

# Champs de PATCH qui n'acceptent pas la valeur null.
NOT_NULLABLE = ("title", "menu", "starts_at", "booking_deadline", "cook_user_id")


def _get_meal(db: Session, meal_id: int, current: CurrentUser) -> models.Meal:
    meal = db.get(models.Meal, meal_id)
    if meal is None or meal.household_id != current.household_id:
        raise HTTPException(status_code=404, detail="meal not found")
    return meal


def _require_cook(meal: models.Meal, current: CurrentUser) -> None:
    if meal.cook_user_id != current.id:
        raise HTTPException(status_code=403, detail="only the cook can do this")


def _require_open(meal: models.Meal) -> None:
    if meal.status != "open":
        raise HTTPException(status_code=409, detail=f"meal is {meal.status}")


@router.get("/meals", response_model=list[schemas.MealOut])
def list_meals(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(models.Meal).where(models.Meal.household_id == current.household_id)
    if from_ is not None:
        stmt = stmt.where(models.Meal.starts_at >= as_utc(from_))
    if to is not None:
        stmt = stmt.where(models.Meal.starts_at <= as_utc(to))
    return db.scalars(stmt.order_by(models.Meal.starts_at, models.Meal.id)).all()


@router.post("/meals", response_model=list[schemas.MealOut], status_code=201)
def create_meal(
    body: schemas.MealCreate,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crée un repas, répété chaque semaine si repeat_weeks > 1."""
    series_id = str(uuid.uuid4()) if body.repeat_weeks > 1 else None
    meals = []
    for week in range(body.repeat_weeks):
        shift = timedelta(weeks=week)
        meal = models.Meal(
            household_id=current.household_id,
            title=body.title.strip(),
            menu=body.menu,
            starts_at=body.starts_at + shift,
            booking_deadline=body.booking_deadline + shift,
            cook_user_id=body.cook_user_id or current.id,
            max_portions=body.max_portions,
            status="open",
            series_id=series_id,
        )
        db.add(meal)
        meals.append(meal)
    db.commit()
    for meal in meals:
        db.refresh(meal)
    return meals


@router.get("/meals/{meal_id}", response_model=schemas.MealOut)
def get_meal(
    meal_id: int,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_meal(db, meal_id, current)


@router.patch("/meals/{meal_id}", response_model=schemas.MealOut)
def update_meal(
    meal_id: int,
    body: schemas.MealUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = _get_meal(db, meal_id, current)
    _require_cook(meal, current)
    _require_open(meal)

    changes = body.model_dump(exclude_unset=True)
    for field in NOT_NULLABLE:
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=400, detail=f"{field} cannot be null")
    starts_at = changes.get("starts_at", as_utc(meal.starts_at))
    deadline = changes.get("booking_deadline", as_utc(meal.booking_deadline))
    if deadline > starts_at:
        raise HTTPException(status_code=400, detail="booking_deadline must not be after starts_at")

    for field, value in changes.items():
        setattr(meal, field, value)
    db.commit()
    db.refresh(meal)
    return meal


@router.post("/meals/{meal_id}/close", response_model=schemas.MealOut)
def close_meal(
    meal_id: int,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = _get_meal(db, meal_id, current)
    _require_cook(meal, current)
    _require_open(meal)
    meal.status = "closed"
    db.commit()
    db.refresh(meal)
    return meal


@router.delete("/meals/{meal_id}", response_model=schemas.MealOut)
def cancel_meal(
    meal_id: int,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = _get_meal(db, meal_id, current)
    _require_cook(meal, current)
    _require_open(meal)
    meal.status = "cancelled"
    db.commit()
    db.refresh(meal)
    return meal
