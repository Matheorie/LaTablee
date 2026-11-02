import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.auth import CurrentUser, get_current_user
from app.db import get_db

router = APIRouter()

# Alphabet sans caractères ambigus (0, O, 1, I).
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _new_invite_code(db: Session) -> str:
    while True:
        code = "TABLE-" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
        taken = db.scalar(select(models.Household.id).where(models.Household.invite_code == code))
        if taken is None:
            return code


def _token_out(user: models.User) -> schemas.TokenOut:
    return schemas.TokenOut(
        access_token=security.create_token(user),
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/auth/register", response_model=schemas.TokenOut, status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.scalar(select(models.User.id).where(models.User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="email already registered")

    if body.invite_code is not None:
        code = body.invite_code.strip().upper()
        household = db.scalar(select(models.Household).where(models.Household.invite_code == code))
        if household is None:
            raise HTTPException(status_code=404, detail="invite code not found")
    else:
        household = models.Household(
            name=body.household_name.strip(), invite_code=_new_invite_code(db)
        )
        db.add(household)
        db.flush()

    user = models.User(
        email=email,
        display_name=body.display_name.strip(),
        password_hash=security.hash_password(body.password),
        household_id=household.id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="email already registered") from None
    db.refresh(user)
    return _token_out(user)


@router.post("/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == body.email.strip().lower()))
    if user is None or not security.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return _token_out(user)


@router.get("/users/me", response_model=schemas.UserOut)
def me(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(models.User, current.id)
    if user is None:
        raise HTTPException(status_code=401, detail="unknown user")
    return user


@router.get("/households/me", response_model=schemas.HouseholdOut)
def my_household(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    household = db.get(models.Household, current.household_id)
    if household is None:
        raise HTTPException(status_code=404, detail="household not found")
    return household


@router.get("/households/me/members", response_model=list[schemas.MemberOut])
def members(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = (
        select(models.User)
        .where(models.User.household_id == current.household_id)
        .order_by(models.User.id)
    )
    return db.scalars(stmt).all()
