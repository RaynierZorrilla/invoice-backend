from fastapi import FastAPI
from config.settings import settings
from routers.client_router import router as client_router
from routers.shipment_router import router as shipment_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(client_router, prefix=settings.API_PREFIX)
app.include_router(shipment_router, prefix=settings.API_PREFIX)

@app.get("/health")
def health():
    return {"status": "ok"}
