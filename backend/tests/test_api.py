# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
# Adjust the import path based on how you run pytest
# If running pytest from the project root: from backend.app.main import app
# If running pytest from the backend directory: from app.main import app
from ..app.main import app # Assuming pytest is run from the 'backend' directory

client = TestClient(app)

# Fixture to clear mock_db before each test that modifies it
@pytest.fixture(autouse=True)
def clear_mock_db_around_tests():
    from ..app.main import mock_db # import locally to modify
    original_db_content = mock_db.copy()
    mock_db.clear()
    yield
    mock_db.clear()
    mock_db.update(original_db_content)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the AI Prompt Engineering Service API!",
        "docs_url": "/docs"
    }

def test_generate_ai_output_success(mocker):
    # Mock the AI service to avoid actual API calls during testing
    mocker.patch(
        # 'backend.app.services.ai_service.get_ai_responses', # If running from root
        'app.services.ai_service.get_ai_responses', # If running from backend/
        return_value=("Casual test response", "Formal test response")
    )

    user_id = "testuser123"
    query = "What is FastAPI?"
    response = client.post("/generate", json={"user_id": user_id, "query": query})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query
    assert data["casual_response"] == "Casual test response"
    assert data["formal_response"] == "Formal test response"
    assert "timestamp" in data

    # Check if data is in mock_db (imported from app.main)
    from ..app.main import mock_db
    assert user_id in mock_db
    assert len(mock_db[user_id]) == 1
    assert mock_db[user_id][0]["query"] == query


def test_generate_ai_output_ai_failure(mocker):
    mocker.patch(
        'app.services.ai_service.get_ai_responses',
        side_effect=Exception("AI service unavailable")
    )
    response = client.post("/generate", json={"user_id": "testuser_fail", "query": "Test query"})
    assert response.status_code == 500
    assert "AI service failed: AI service unavailable" in response.json()["detail"]


def test_get_user_history_found(mocker):
    # Mock AI service for populating history
    mocker.patch(
        'app.services.ai_service.get_ai_responses',
        return_value=("Casual hist", "Formal hist")
    )

    user_id = "history_user"
    # Populate some history
    client.post("/generate", json={"user_id": user_id, "query": "Query 1"})
    client.post("/generate", json={"user_id": user_id, "query": "Query 2"})

    response = client.get(f"/history?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert "interactions" in data
    assert len(data["interactions"]) == 2
    assert data["interactions"][0]["query"] == "Query 2" # Newest first
    assert data["interactions"][1]["query"] == "Query 1"

def test_get_user_history_not_found():
    response = client.get("/history?user_id=nonexistentuser")
    assert response.status_code == 200 # API returns 200 with empty list as per spec
    data = response.json()
    assert data["interactions"] == []

def test_get_user_history_no_userid():
    response = client.get("/history") # Missing user_id query parameter
    assert response.status_code == 422 # FastAPI validation error for missing required query param
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["type"] == "missing"
    assert data["detail"][0]["loc"] == ["query", "user_id"]

# To run tests:
# 1. Navigate to the `backend` directory.
# 2. Ensure `pytest` and `pytest-mock` (mocker) are installed (add to backend/requirements.txt if not).
#    `pip install pytest pytest-mock`
# 3. Run: `python -m pytest` or simply `pytest`
