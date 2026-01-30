import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.core.config import SETTINGS # Configuration like API Keys

app = FastAPI(
    title="IntelliCredit Memory Pipeline",
    description="AI-Driven Credit Risk & Fraud Detection with Vector Memory",
    version="1.0.0"
)

# Enable CORS for the Streamlit Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with dashboard URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include our API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"status": "online", "message": "IntelliCredit API is running"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)