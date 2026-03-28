"""Internal API routes for triggering scrapes and checking status."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "receiptwitness"}
