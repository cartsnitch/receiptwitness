"""Shopping routes: optimize list, saved lists."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError, RequestError

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.schemas import OptimizeRequest, OptimizeResponse, ShoppingListResponse
from cartsnitch_api.services.clipartist import ClipArtistClient

router = APIRouter(prefix="/shopping", tags=["shopping"])


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_shopping(body: OptimizeRequest, user_id: UUID = Depends(get_current_user)):
    client = ClipArtistClient()
    try:
        result = await client.optimize(
            user_id=str(user_id),
            items=[item.model_dump() for item in body.items],
            preferred_stores=(
                [str(s) for s in body.preferred_stores] if body.preferred_stores else None
            ),
        )
        return result
    except HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail="Shopping optimization service error",
        ) from e
    except RequestError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach shopping optimization service",
        ) from None


@router.get("/lists", response_model=list[ShoppingListResponse])
async def list_shopping_lists(user_id: UUID = Depends(get_current_user)):
    client = ClipArtistClient()
    try:
        return await client.get_shopping_lists(str(user_id))
    except (HTTPStatusError, RequestError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach shopping service",
        ) from None
