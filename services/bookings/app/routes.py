from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import clients, models, schemas
from app.auth import CurrentUser, get_current_user
from app.db import get_db

router = APIRouter()


def _parse_date(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _open_meal(meal_id: int, current: CurrentUser) -> dict:
    """Interroge meals : le repas doit exister, appartenir à la colocation, être ouvert
    et avoir sa date limite d'inscription dans le futur."""
    meal = clients.fetch_meal(meal_id, current.token)
    if meal["status"] != "open":
        raise HTTPException(status_code=409, detail=f"meal is {meal['status']}")
    if _parse_date(meal["booking_deadline"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="booking deadline passed")
    return meal


def _find_booking(db: Session, meal_id: int, user_id: int) -> models.Booking | None:
    return db.scalar(
        select(models.Booking).where(
            models.Booking.meal_id == meal_id, models.Booking.user_id == user_id
        )
    )


@router.put("/bookings/meals/{meal_id}", response_model=schemas.BookingOut)
def put_booking(
    meal_id: int,
    body: schemas.BookingIn,
    response: Response,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = _open_meal(meal_id, current)
    booking = _find_booking(db, meal_id, current.id)

    if meal["max_portions"] is not None:
        taken = db.scalar(
            select(func.coalesce(func.sum(models.Booking.portions), 0)).where(
                models.Booking.meal_id == meal_id, models.Booking.user_id != current.id
            )
        )
        if taken + body.portions > meal["max_portions"]:
            raise HTTPException(status_code=409, detail="meal is full")

    if booking is None:
        booking = models.Booking(meal_id=meal_id, user_id=current.id, portions=body.portions)
        db.add(booking)
        response.status_code = 201
    else:
        booking.portions = body.portions
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="booking already exists") from None
    db.refresh(booking)
    return booking


@router.delete("/bookings/meals/{meal_id}", status_code=204)
def delete_booking(
    meal_id: int,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _open_meal(meal_id, current)
    booking = _find_booking(db, meal_id, current.id)
    if booking is None:
        raise HTTPException(status_code=404, detail="booking not found")
    db.delete(booking)
    db.commit()
    return Response(status_code=204)


@router.get("/bookings/meals/{meal_id}", response_model=schemas.MealBookingsOut)
def meal_bookings(
    meal_id: int,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Vérifie que le repas existe dans la colocation de l'appelant.
    clients.fetch_meal(meal_id, current.token)
    rows = db.scalars(
        select(models.Booking)
        .where(models.Booking.meal_id == meal_id)
        .order_by(models.Booking.user_id)
    ).all()
    return schemas.MealBookingsOut(
        meal_id=meal_id,
        total_portions=sum(r.portions for r in rows),
        participants=[schemas.ParticipantOut(user_id=r.user_id, portions=r.portions) for r in rows],
    )


@router.get("/bookings/me", response_model=list[schemas.BookingOut])
def my_bookings(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mes inscriptions à venir : repas non annulés dont la date n'est pas passée."""
    rows = db.scalars(
        select(models.Booking)
        .where(models.Booking.user_id == current.id)
        .order_by(models.Booking.meal_id)
    ).all()
    now = datetime.now(timezone.utc)
    upcoming = []
    for row in rows:
        try:
            meal = clients.fetch_meal(row.meal_id, current.token)
        except HTTPException as exc:
            if exc.status_code == 404:
                continue
            raise
        if meal["status"] != "cancelled" and _parse_date(meal["starts_at"]) >= now:
            upcoming.append(row)
    return upcoming
