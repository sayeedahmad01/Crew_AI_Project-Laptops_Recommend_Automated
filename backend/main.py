import os
import sys
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Ensure both repository root and backend directory are on the import path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
for path in (BASE_DIR, BACKEND_DIR):
    if path not in sys.path:
        sys.path.append(path)

from backend.data_manager import clean_dataset, get_dataset_stats, get_laptops_data
from backend.crew import create_laptop_crew

app = FastAPI(
    title="AI Laptop Recommendation System",
    description="CrewAI and FastAPI Laptop Recommendation Dashboard",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class RecommendRequest(BaseModel):
    provider: str  # 'openai' or 'gemini'
    major: str
    budget: float
    ram: Optional[float] = None
    brand: Optional[str] = "Any"
    os_name: Optional[str] = "Any"
    details: Optional[str] = ""

class CleanRequest(BaseModel):
    pass

# API Endpoints

@app.post("/api/clean")
def clean_data():
    """Trigger the data cleaning process on the raw dataset."""
    try:
        res = clean_dataset()
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data cleaning failed: {str(e)}")

@app.get("/api/stats")
def get_stats():
    """Retrieve statistics about the cleaned dataset."""
    try:
        stats = get_dataset_stats()
        if "error" in stats:
            raise HTTPException(status_code=400, detail=stats["error"])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/api/laptops")
def get_laptops():
    """Retrieve all cleaned laptops in the database."""
    try:
        return get_laptops_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load laptops list: {str(e)}")

@app.post("/api/recommend")
def recommend_laptops(
    req: RecommendRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Run CrewAI agents to recommend laptops based on student major and specs.
    Runs synchronously (in FastAPI's threadpool) to prevent blocking the event loop.
    """
    provider = req.provider.lower()
    
    # Retrieve key from header or fallback to env
    api_key = x_api_key
    if not api_key:
        if provider == 'gemini':
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        elif provider == 'openai':
            api_key = os.environ.get("OPENAI_API_KEY")
        elif provider in ('kimi', 'nvidia_kimi'):
            api_key = os.environ.get("NVIDIA_API_KEY") or "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"
            
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail=f"API Key for {provider} was not supplied. Please set it in the UI or server environment variables."
        )

    # Build profile dict
    user_profile = {
        "major": req.major,
        "budget": req.budget,
        "ram": req.ram if req.ram else "Any",
        "brand": req.brand if req.brand else "Any",
        "os": req.os_name if req.os_name else "Any",
        "details": req.details if req.details else "None"
    }

    try:
        # Create Crew
        crew = create_laptop_crew(api_key=api_key, provider=provider, user_profile=user_profile)
        
        # Execute the recommendation task
        # This will query using dataset tools and analyze options
        result = crew.kickoff()
        
        # CrewAI returns a CrewOutput object, which contains raw string output
        # Let's extract the text output
        result_text = getattr(result, "raw", str(result))
        
        return {
            "status": "success",
            "recommendation": result_text
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"CrewAI execution failed: {str(e)}")

# Mount Static Files (Frontend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(BASE_DIR, "frontend")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    # If frontend folder is not created yet, serve dummy message
    @app.get("/")
    def read_root_dummy():
        return HTMLResponse("<h1>Laptop Recommendation Backend</h1><p>Frontend assets are not yet written.</p>")
