
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

app = FastAPI(
    title="Wardrobe AI",
    description="API para organização de guarda-roupa e recomendações de looks.",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Hello, World! Wardrobe AI API está funcionando!",
        "status": "online"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected"
            }
        )
