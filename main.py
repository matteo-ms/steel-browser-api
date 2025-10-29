"""
Steel Browser API - FastAPI Server
REST API for web scraping with Steel Browser on Railway
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

from steel_scraper import SteelBrowserScraper

# Initialize FastAPI app
app = FastAPI(
    title="Steel Browser API",
    description="Advanced web scraping API with Google search and deep content extraction",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get Steel Browser URL from environment variable
STEEL_URL = os.getenv("STEEL_URL", "https://steel-browser-production-9a2a.up.railway.app")


# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query", example="Juventus vs Inter formazioni")
    language: str = Field(default="it", description="Search language", example="it")
    region: str = Field(default="it", description="Search region", example="it")
    search_type: str = Field(default="web", description="Search type: web or news", example="news")
    time_filter: Optional[str] = Field(
        default=None, 
        description="Time filter: hour, day, 3days, week, month, year",
        example="3days"
    )
    num_results: int = Field(default=5, ge=1, le=20, description="Number of results to scrape", example=5)

    class Config:
        schema_extra = {
            "example": {
                "query": "Juventus vs Inter formazioni probabili",
                "language": "it",
                "region": "it",
                "search_type": "news",
                "time_filter": "3days",
                "num_results": 5
            }
        }


class ScrapedResult(BaseModel):
    position: int
    search_title: str
    url: str
    page_title: str
    headings: List[str]
    paragraphs: List[str]
    main_text: str
    metadata: Dict[str, Any]
    error: Optional[str]
    scraped_at: str


class SearchResponse(BaseModel):
    query: str
    language: str
    region: str
    search_type: str
    time_filter: Optional[str]
    scraped_at: str
    total_results: int
    results: List[ScrapedResult]


class HealthResponse(BaseModel):
    status: str
    steel_url: str
    timestamp: str


# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Steel Browser API",
        "version": "1.0.0",
        "description": "Advanced web scraping API with Steel Browser",
        "endpoints": {
            "health": "/health",
            "search": "/search (POST)",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        steel_url=STEEL_URL,
        timestamp=datetime.now().isoformat()
    )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_and_scrape(request: SearchRequest):
    """
    Perform advanced Google search and deep scrape each result
    
    This endpoint:
    1. Performs a Google search with specified filters (language, region, time, type)
    2. Extracts URLs from search results
    3. Visits each URL and extracts full content (titles, headings, paragraphs, text)
    4. Returns structured data with all extracted information
    
    Parameters:
    - **query**: Search query string
    - **language**: Interface and results language (it, en, es, fr, de, nl, etc.)
    - **region**: Geographic region for results (it, us, uk, de, fr, etc.)
    - **search_type**: Type of search - "web" for regular search, "news" for news search
    - **time_filter**: Optional time filter (hour, day, 3days, week, month, year)
    - **num_results**: Number of results to scrape (1-20, default: 5)
    
    Returns:
    - Complete scraped data including titles, full text, headings, paragraphs, and metadata
    """
    try:
        # Validate inputs
        if request.search_type not in ['web', 'news']:
            raise HTTPException(status_code=400, detail="search_type must be 'web' or 'news'")
        
        valid_time_filters = ['hour', 'day', '3days', 'week', 'month', 'year', None]
        if request.time_filter not in valid_time_filters:
            raise HTTPException(
                status_code=400, 
                detail=f"time_filter must be one of: {', '.join([str(f) for f in valid_time_filters if f])}"
            )
        
        # Initialize scraper
        scraper = SteelBrowserScraper(STEEL_URL)
        
        # Perform search and scraping
        results = await scraper.search_and_extract(
            query=request.query,
            language=request.language,
            region=request.region,
            search_type=request.search_type,
            time_filter=request.time_filter,
            num_results=request.num_results
        )
        
        # Build response
        return SearchResponse(
            query=request.query,
            language=request.language,
            region=request.region,
            search_type=request.search_type,
            time_filter=request.time_filter,
            scraped_at=datetime.now().isoformat(),
            total_results=len(results),
            results=[ScrapedResult(**result) for result in results]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


# For local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

