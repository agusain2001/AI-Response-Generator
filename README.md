# AI Response Generator

A web application that generates both casual and formal AI responses to user queries using Google's Gemini API.

## Project Structure

- **Backend**: FastAPI application that interfaces with Google's Gemini API
- **Frontend**: Streamlit application that provides a user interface

## Deployment

This application is deployed in two parts:

1. **Frontend**: Deployed on Streamlit Cloud
2. **Backend**: Deployed on Render

### Environment Variables

The following environment variables need to be set in your deployment platforms:

- `GOOGLE_API_KEY`: Your Google Gemini API key
- `BACKEND_API_URL`: URL of your deployed backend (set in Netlify for the frontend)

## Local Development

### Prerequisites

- Python 3.9+
- Google Gemini API key

### Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r main_requirements.txt
   ```
3. Create a `.env` file in the root directory with your Google Gemini API key:
   ```
   GOOGLE_API_KEY="your-api-key"
   ```

### Running Locally

1. Start the backend:
   ```
   cd backend
   uvicorn app.main:app --reload
   ```

2. Start the frontend in a separate terminal:
   ```
   cd fronted
   streamlit run app.py
   ```

3. Access the application at http://localhost:8501

## API Endpoints

- `POST /generate`: Generate AI responses for a query
- `GET /history`: Get interaction history for a user
- `GET /`: Root endpoint with welcome message

## Security Notes

- The Google API key should be kept secure and not exposed in client-side code
- For production, consider implementing proper authentication
