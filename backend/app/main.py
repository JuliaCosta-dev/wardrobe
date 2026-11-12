
from fastapi import FastAPI

app = FastAPI(
    title="Wardrobe AI",
    description="APi para organização de guarda-roupa e recomendações de looks",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "message": " Hello, World! Wardrobe AI API está funcionando!",
        "status": "online"
    }
    
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }