"""FastAPI app entrypoint for ReceiptWitness."""

from fastapi import FastAPI

from receiptwitness.api.routes import router

app = FastAPI(title="ReceiptWitness", version="0.1.0")
app.include_router(router)
