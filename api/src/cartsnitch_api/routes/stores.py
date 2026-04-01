"""Store routes: list stores, manage user store connections."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from cartsnitch_api.auth.dependencies import get_current_user
from cartsnitch_api.database import get_db
from cartsnitch_api.schemas import ConnectStoreRequest, StoreAccountResponse, StoreResponse
from cartsnitch_api.services.stores import StoreService

router = APIRouter(tags=["stores"])


@router.get("/stores", response_model=list[StoreResponse])
async def list_stores(db: AsyncSession = Depends(get_db)):
    svc = StoreService(db)
    return await svc.list_stores()


@router.get("/me/stores", response_model=list[StoreAccountResponse])
async def list_user_stores(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StoreService(db)
    return await svc.list_user_stores(user_id)


@router.post(
    "/me/stores/{store_slug}/connect",
    response_model=StoreAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def connect_store(
    store_slug: str,
    body: ConnectStoreRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StoreService(db)
    try:
        return await svc.connect_store(user_id, store_slug, body.credentials)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/me/stores/{store_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_store(
    store_slug: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StoreService(db)
    try:
        await svc.disconnect_store(user_id, store_slug)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
