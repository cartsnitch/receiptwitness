"""User routes: per-user account endpoints (email-in address, etc.)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.database import get_db
from cartsnitch_api.schemas import EmailInAddressResponse
from cartsnitch_api.services.auth import AuthService

router = APIRouter(tags=["user"])


@router.get("/me/email-in-address", response_model=EmailInAddressResponse)
async def get_email_in_address(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    try:
        email_address = await svc.get_email_in_address(user_id)
        return EmailInAddressResponse(email_address=email_address)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        ) from None
