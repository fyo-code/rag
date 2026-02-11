"""
FastAPI Backend for SQL-First RAG Chatbot
Exposes endpoints for chat, schema, and statistics
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from database import init_database, get_schema, get_stats, get_sample_data
from sql_agent import chat

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    print("🚀 Starting SQL-First RAG Backend...")
    init_database()
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Reclamații RAG API",
    description="SQL-First RAG Chatbot for Mobexpert Complaints Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    text: str
    visualization: str = "none"
    data: list = []
    columns: list = []
    sql: str | None = None
    row_count: int = 0
    chart_config: dict | None = None
    error: bool = False


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "reclamatii-rag"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint.
    Accepts natural language question, returns formatted response with data.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        result = chat(request.message)
        return ChatResponse(**result)
    except Exception as e:
        return ChatResponse(
            text=f"Eroare internă: {str(e)}",
            error=True
        )


@app.get("/api/schema")
async def schema_endpoint():
    """Return database schema for reference."""
    return {"schema": get_schema()}


@app.get("/api/stats")
async def stats_endpoint():
    """Return dashboard statistics."""
    try:
        stats = get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sample")
async def sample_endpoint():
    """Return sample data rows."""
    try:
        return {"data": get_sample_data()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
