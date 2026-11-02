import httpx
from fastapi import HTTPException

from app import config


def get_json(url: str, token: str):
    """GET vers un autre service avec le jeton de l'appelant.

    Délai maximal de 3 secondes. Service injoignable ou en erreur : 503.
    """
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=config.SERVICE_TIMEOUT,
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="upstream service unavailable") from None
    if response.status_code in (401, 403, 404):
        raise HTTPException(status_code=response.status_code, detail="upstream refused")
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="upstream service error")
    return response.json()


def fetch_meal(meal_id: int, token: str) -> dict:
    return get_json(f"{config.MEALS_URL}/meals/{meal_id}", token)


def fetch_participants(meal_id: int, token: str) -> dict:
    return get_json(f"{config.BOOKINGS_URL}/bookings/meals/{meal_id}", token)
