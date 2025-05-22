
from pydantic import BaseModel
from typing import List, Optional
import datetime

class GenerateRequest(BaseModel):
    """
    Request model for the /generate endpoint.
    """
    user_id: str
    query: str

class GenerateResponse(BaseModel):
    """
    Response model for a single interaction record.
    Used by /generate endpoint response and as an item in /history response.
    """
    query: str
    casual_response: str
    formal_response: str
    timestamp: datetime.datetime # Store as datetime, will be serialized to string by FastAPI

class HistoryResponse(BaseModel):
    """
    Response model for the /history endpoint.
    Contains a list of past interactions.
    """
    interactions: List[GenerateResponse]

# In-memory storage for demonstration (replace with DB later)
# This will store GenerateResponse like objects, but for simplicity,
# we'll store dictionaries that match the structure.
# Each user_id will map to a list of their interactions.
mock_db: dict[str, List[dict]] = {}
