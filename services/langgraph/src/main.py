"""
LangGraph Story Generation Service

This FastAPI service handles the AI story generation using LangGraph.
It exposes REST endpoints that can be called by the Flask API service.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from src.core.story_teller import StoryTeller
from src.core.logger import Logger
from src.schemas.story_config import StoryTellerItem


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Models for API
# ---------------------------------------------------------------------------

class ChampionInput(BaseModel):
    """Input model for a champion character."""
    name: str = Field(..., description="Champion name (e.g., 'Zed', 'TwistedFate')")
    personality: str = Field(..., description="Personality traits")
    models: str = Field(default="grok_4", description="Model to use for this champion")


class StoryGenerationRequest(BaseModel):
    """Request model for story generation."""
    scenario: str = Field(..., description="The story scenario/premise")
    champions: List[ChampionInput] = Field(..., description="List of champions")


class StoryGenerationResponse(BaseModel):
    """Response model for story generation."""
    success: bool
    story: Optional[str] = None
    error: Optional[str] = None
    scenario_used: Optional[str] = None
    champions_used: Optional[List[Dict[str, Any]]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting LangGraph Story Generation Service...")
    yield
    logger.info("Shutting down LangGraph Story Generation Service...")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="LangGraph Story Generation Service",
    description="AI-powered story generation using LangGraph with multiple AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run."""
    return HealthResponse(
        status="healthy",
        service="langgraph-story-generator",
        version="1.0.0",
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "LangGraph Story Generation Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate": "/generate (POST)",
        },
    }


@app.post("/generate", response_model=StoryGenerationResponse)
async def generate_story(request: StoryGenerationRequest):
    """
    Generate a story using LangGraph.
    
    This endpoint orchestrates multiple AI agents to create a cohesive narrative
    based on the provided scenario and champion characters.
    """
    logger.info(f"Received story generation request: scenario='{request.scenario[:50]}...'")
    logger.info(f"Champions: {[c.name for c in request.champions]}")
    
    try:
        # Convert request to internal format
        champions_data = [
            {
                "name": champion.name,
                "personality": champion.personality,
                "models": champion.models,
            }
            for champion in request.champions
        ]
        
        # Create logger and story teller
        story_logger = Logger()
        story_teller = StoryTeller(
            StoryTellerItem(
                scenario=request.scenario,
                champions=champions_data,
                logger=story_logger,
            )
        )
        
        # Build and run the graph
        story_teller.build_graph()
        result = story_teller.invoke()
        
        logger.info("Story generation completed successfully")
        
        return StoryGenerationResponse(
            success=True,
            story=result,
            scenario_used=request.scenario,
            champions_used=champions_data,
        )
        
    except Exception as e:
        logger.error(f"Story generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Story generation failed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "production") == "development",
    )

