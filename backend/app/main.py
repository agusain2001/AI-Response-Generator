# backend/app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import datetime
import uuid # For generating unique IDs if needed for interactions (though not part of schema yet)

from .models.schemas import GenerateRequest, GenerateResponse, HistoryResponse
from .services.ai_service import get_ai_responses

# In-memory storage for demonstration (replace with DB later)
# Each user_id maps to a list of their interactions (GenerateResponse like dicts)
mock_db: Dict[str, List[Dict]] = {}

app = FastAPI(
    title="AI Prompt Engineering Service",
    description="API for generating AI responses and managing interaction history.",
    version="0.1.0"
)

# Configure CORS
# Allows requests from Streamlit frontend (typically running on http://localhost:8501)
origins = [
    "http://localhost",
    "http://localhost:8501", # Default Streamlit port
    # Add other origins if needed, e.g., your deployed frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

@app.post("/generate", response_model=GenerateResponse, tags=["AI Generation"])
async def generate_ai_output(request: GenerateRequest):
    """
    Accepts a user ID and a query, generates casual and formal AI responses.
    (Currently stores interaction in-memory).
    """
    try:
        casual_res, formal_res = await get_ai_responses(request.query)
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"AI service failed: {str(e)}")

    timestamp = datetime.datetime.now(datetime.timezone.utc)
    
    interaction_data = {
        "query": request.query,
        "casual_response": casual_res,
        "formal_response": formal_res,
        "timestamp": timestamp.isoformat() # Store as ISO string for consistency
    }

    # Store in our mock_db
    if request.user_id not in mock_db:
        mock_db[request.user_id] = []
    
    # We need to convert the interaction_data to a model that can be appended
    # Or ensure mock_db stores objects that match GenerateResponse fields
    # For simplicity, we'll store dicts and construct GenerateResponse for the return
    
    # Create a dictionary that can be easily converted back to GenerateResponse if needed
    # Note: Pydantic models expect datetime objects, not ISO strings for datetime fields
    # when creating an instance. So, we pass the `timestamp` object.
    db_entry = {
        "query": request.query,
        "casual_response": casual_res,
        "formal_response": formal_res,
        "timestamp": timestamp # Store datetime object in mock_db for easier sorting
    }
    mock_db[request.user_id].append(db_entry)
    
    # Return a GenerateResponse model instance
    return GenerateResponse(
        query=request.query,
        casual_response=casual_res,
        formal_response=formal_res,
        timestamp=timestamp
    )


@app.get("/history", response_model=HistoryResponse, tags=["Interaction History"])
async def get_user_history(user_id: str = Query(..., description="The ID of the user whose history is to be retrieved.")):
    """
    Returns all past interactions for the given user in reverse chronological order.
    (Retrieves from in-memory store).
    """
    if user_id not in mock_db:
        # Return an empty list of interactions if user_id not found
        return HistoryResponse(interactions=[])

    user_interactions_dicts = mock_db.get(user_id, [])
    
    # Sort interactions by timestamp in reverse chronological order (newest first)
    # The timestamp is stored as a datetime object in mock_db
    sorted_interactions = sorted(
        user_interactions_dicts,
        key=lambda x: x["timestamp"],
        reverse=True
    )
    
    # Convert list of dicts to list of GenerateResponse model instances
    # FastAPI will automatically convert datetime to ISO string in the JSON response
    interactions_models = [
        GenerateResponse(
            query=item["query"],
            casual_response=item["casual_response"],
            formal_response=item["formal_response"],
            timestamp=item["timestamp"]
        ) for item in sorted_interactions
    ]
    
    return HistoryResponse(interactions=interactions_models)

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint for the API.
    Provides a welcome message and link to the API documentation.
    """
    return {
        "message": "Welcome to the AI Prompt Engineering Service API!",
        "docs_url": "/docs"
    }

# Placeholder for tests directory and files
# backend/tests/__init__.py (empty)
# backend/tests/test_api.py (basic structure)
# backend/tests/test_services.py (basic structure)

if __name__ == "__main__":
    # This part is for running with `python app/main.py` for simple testing,
    # but `uvicorn app.main:app --reload` is preferred for development.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
