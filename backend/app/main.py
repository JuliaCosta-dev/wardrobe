from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.auth import router as auth_router
from app.api.v1.garment_images import router as garment_images_router
from app.api.v1.garments import router as garments_router
from app.api.v1.outfits import router as outfits_router
from app.api.v1.profile import router as profile_router
from app.api.v1.recommendation_feedback import router as recommendation_feedback_router
from app.api.v1.recommendations import router as recommendations_router
from app.database import engine

app = FastAPI(
    title="Wardrobe AI",
    description="API para organização de guarda-roupa e recomendações de looks.",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(garments_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(garment_images_router, prefix="/api/v1")
app.include_router(outfits_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(recommendation_feedback_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Hello, World! Wardrobe AI API está funcionando!", "status": "online"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "healthy", "database": "connected"}

    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "database": "disconnected"}
        )
