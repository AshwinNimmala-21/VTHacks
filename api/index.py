# This file is needed for Vercel to recognize the API routes
# It imports the main FastAPI app from the backend directory
import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import the FastAPI app
from main import app

# Export the app for Vercel
handler = app
