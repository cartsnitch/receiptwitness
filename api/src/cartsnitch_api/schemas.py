"""Pydantic v2 request/response schemas for all API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ---------- Auth ----------
# Registration, login, and session management are handled by Better-Auth (auth/ service).
# These schemas are for the profile management endpoints only.


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = Field(None, min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    created_at: datetime


class EmailInAddressResponse(BaseModel):
    email_address: str


# ---------- Stores ----------


class StoreResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: str | None = None
    supported: bool = True


class StoreAccountResponse(BaseModel):
    store: StoreResponse
    connected: bool
    last_sync_at: datetime | None = None
    sync_status: str | None = None


class ConnectStoreRequest(BaseModel):
    credentials: dict | None = None


# ---------- Purchases ----------


class LineItemResponse(BaseModel):
    id: UUID
    product_id: UUID | None = None
    name: str
    quantity: float
    unit_price: float
    total_price: float


class PurchaseResponse(BaseModel):
    id: UUID
    store_id: UUID
    store_name: str
    purchased_at: datetime
    total: float
    item_count: int


class PurchaseDetailResponse(PurchaseResponse):
    line_items: list[LineItemResponse]


class PurchaseStatsResponse(BaseModel):
    total_spent: float
    purchase_count: int
    by_store: dict[str, float]
    by_period: dict[str, float]


# ---------- Products ----------


class ProductResponse(BaseModel):
    id: UUID
    name: str
    brand: str | None = None
    category: str | None = None
    upc: str | None = None
    image_url: str | None = None


class ProductDetailResponse(ProductResponse):
    prices_by_store: list["StorePriceResponse"]


class StorePriceResponse(BaseModel):
    store_id: UUID
    store_name: str
    current_price: float
    last_seen_at: datetime


# ---------- Prices ----------


class PriceTrendResponse(BaseModel):
    product_id: UUID
    product_name: str
    data_points: list["PricePointResponse"]


class PricePointResponse(BaseModel):
    date: datetime
    price: float
    store_id: UUID
    store_name: str


class PriceIncreaseResponse(BaseModel):
    product_id: UUID
    product_name: str
    store_name: str
    old_price: float
    new_price: float
    increase_pct: float
    detected_at: datetime


class PriceComparisonResponse(BaseModel):
    product_id: UUID
    product_name: str
    prices: list[StorePriceResponse]


# ---------- Coupons ----------


class CouponResponse(BaseModel):
    id: UUID
    store_id: UUID
    store_name: str
    description: str
    discount_value: float
    discount_type: str
    product_id: UUID | None = None
    expires_at: datetime | None = None


# ---------- Shopping ----------


class ShoppingListItemRequest(BaseModel):
    product_id: UUID | None = None
    name: str
    quantity: int = 1


class OptimizeRequest(BaseModel):
    items: list[ShoppingListItemRequest]
    preferred_stores: list[UUID] | None = None


class OptimizedStoreTrip(BaseModel):
    store_id: UUID
    store_name: str
    items: list["OptimizedItemResponse"]
    subtotal: float
    coupons: list[CouponResponse]
    savings: float


class OptimizedItemResponse(BaseModel):
    name: str
    price: float
    product_id: UUID | None = None


class OptimizeResponse(BaseModel):
    trips: list[OptimizedStoreTrip]
    total_cost: float
    total_savings: float


class ShoppingListResponse(BaseModel):
    id: UUID
    name: str
    item_count: int
    created_at: datetime
    updated_at: datetime


# ---------- Alerts ----------


class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    product_id: UUID
    product_name: str
    message: str
    triggered_at: datetime
    read: bool = False


class AlertSettingsRequest(BaseModel):
    price_increase_threshold_pct: float | None = None
    shrinkflation_enabled: bool | None = None
    email_notifications: bool | None = None


class AlertSettingsResponse(BaseModel):
    price_increase_threshold_pct: float
    shrinkflation_enabled: bool
    email_notifications: bool


# ---------- Scraping ----------


class SyncTriggerResponse(BaseModel):
    job_id: UUID
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    store_slug: str
    status: str
    last_sync_at: datetime | None = None
    items_synced: int | None = None


# ---------- Public ----------


class PublicTrendResponse(BaseModel):
    product_id: UUID
    product_name: str
    data_points: list[PricePointResponse]


class PublicStoreComparisonResponse(BaseModel):
    products: list[PriceComparisonResponse]


class PublicInflationResponse(BaseModel):
    period: str
    cartsnitch_index: float
    cpi_baseline: float
    categories: dict[str, float]


# ---------- Common ----------


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


# Rebuild forward refs
ProductDetailResponse.model_rebuild()
PriceTrendResponse.model_rebuild()
OptimizedStoreTrip.model_rebuild()
