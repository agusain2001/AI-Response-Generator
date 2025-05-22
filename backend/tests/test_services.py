# backend/tests/test_services.py
import pytest
import os
# Adjust import path based on how pytest is run
# from backend.app.services.ai_service import get_ai_responses, generate_text_gemini
from ..app.services import ai_service # Assuming pytest is run from the 'backend' directory

# Check if API key is available to decide if live API tests should run
# It's better to mock API calls in unit tests.
# These tests might become integration tests if they hit the actual API.
GEMINI_API_KEY_EXISTS = bool(os.getenv("GOOGLE_API_KEY"))

@pytest.mark.asyncio
async def test_generate_text_gemini_mocked(mocker):
    """
    Tests the generate_text_gemini function with a mocked Gemini API call.
    """
    mock_gemini_model = mocker.MagicMock()
    mock_response = mocker.MagicMock()

    # Simulate a successful response structure from Gemini API
    mock_part = mocker.MagicMock()
    mock_part.text = "Mocked AI response"
    mock_candidate = mocker.MagicMock()
    mock_candidate.content.parts = [mock_part]
    mock_response.candidates = [mock_candidate]
    mock_response.prompt_feedback = None # No blocking

    # Configure the model's async method to return the mock response
    mock_gemini_model.generate_content_async.return_value = mock_response
    
    # Patch the 'model' instance in ai_service module
    mocker.patch('app.services.ai_service.model', mock_gemini_model)
    mocker.patch('app.services.ai_service.GEMINI_API_KEY', "fake_key_for_test") # Ensure it thinks key exists


    prompt = "Test prompt"
    result = await ai_service.generate_text_gemini(prompt)

    assert result == "Mocked AI response"
    mock_gemini_model.generate_content_async.assert_called_once_with(prompt)

@pytest.mark.asyncio
async def test_generate_text_gemini_blocked_prompt_mocked(mocker):
    """
    Tests generate_text_gemini when the prompt is blocked by safety settings.
    """
    mock_gemini_model = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    
    mock_response.prompt_feedback = mocker.MagicMock()
    mock_response.prompt_feedback.block_reason = "SAFETY"
    mock_response.candidates = [] # No candidates if blocked

    mock_gemini_model.generate_content_async.return_value = mock_response
    mocker.patch('app.services.ai_service.model', mock_gemini_model)
    mocker.patch('app.services.ai_service.GEMINI_API_KEY', "fake_key_for_test")

    prompt = "Blocked test prompt"
    result = await ai_service.generate_text_gemini(prompt)

    assert "Content generation failed: Prompt was blocked due to SAFETY" in result

@pytest.mark.asyncio
async def test_generate_text_gemini_api_error_mocked(mocker):
    """
    Tests generate_text_gemini when the API call raises an exception.
    """
    mock_gemini_model = mocker.MagicMock()
    mock_gemini_model.generate_content_async.side_effect = Exception("Generic API Error")
    
    mocker.patch('app.services.ai_service.model', mock_gemini_model)
    mocker.patch('app.services.ai_service.GEMINI_API_KEY', "fake_key_for_test")

    prompt = "Error test prompt"
    result = await ai_service.generate_text_gemini(prompt)
    
    assert "Error: AI service request failed. Details: Generic API Error" in result

@pytest.mark.asyncio
async def test_get_ai_responses_mocked(mocker):
    """
    Tests the get_ai_responses function, ensuring it calls generate_text_gemini for
    both casual and formal prompts.
    """
    # Mock generate_text_gemini within the ai_service module
    mock_generate = mocker.patch('app.services.ai_service.generate_text_gemini')
    
    # Define different return values for sequential calls
    mock_generate.side_effect = ["Mocked casual response", "Mocked formal response"]

    user_query = "Test query for responses"
    casual_res, formal_res = await ai_service.get_ai_responses(user_query)

    assert casual_res == "Mocked casual response"
    assert formal_res == "Mocked formal response"
    
    assert mock_generate.call_count == 2
    
    # Check the prompts passed to generate_text_gemini
    # First call (casual)
    call_args_casual = mock_generate.call_args_list[0][0][0] # Gets the first positional argument of the first call
    assert f'A user asked: "{user_query}"' in call_args_casual
    assert "casual, easy-to-understand" in call_args_casual

    # Second call (formal)
    call_args_formal = mock_generate.call_args_list[1][0][0] # Gets the first positional argument of the second call
    assert f'Regarding the query: "{user_query}"' in call_args_formal
    assert "formal, structured, and analytical" in call_args_formal


@pytest.mark.skipif(not GEMINI_API_KEY_EXISTS, reason="GOOGLE_API_KEY not set, skipping live API test.")
@pytest.mark.asyncio
async def test_generate_text_gemini_live_call_short():
    """
    A simple live test for generate_text_gemini.
    This test will make an actual API call to Gemini.
    Only run if GOOGLE_API_KEY is configured.
    """
    # Ensure the actual model is used, not a mock
    if not ai_service.model or not ai_service.GEMINI_API_KEY:
        pytest.skip("Gemini model or API key not properly initialized in ai_service.")

    prompt = "Say 'Hello'"
    try:
        result = await ai_service.generate_text_gemini(prompt)
        print(f"Live API response for '{prompt}': {result}") # For visibility during test run
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Error:" not in result # Basic check for no error message
    except Exception as e:
        pytest.fail(f"Live API call failed with exception: {e}")

# To run these tests:
# 1. Navigate to the `backend` directory.
# 2. Ensure `pytest`, `pytest-mock`, and `pytest-asyncio` are installed.
#    `pip install pytest pytest-mock pytest-asyncio`
# 3. Run: `python -m pytest` or `pytest`
# Note: Add `pytest-asyncio` to backend/requirements.txt for test dependencies.
