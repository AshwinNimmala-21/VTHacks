# This file is needed for Vercel to recognize the API routes
# It imports the main FastAPI app from the same directory
import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

# Add the backend directory to the Python path for imports
backend_path = os.path.join(current_dir, '..', 'backend')
sys.path.insert(0, backend_path)

try:
    # Import the FastAPI app from the copied main.py
    from main import app
    print("Successfully imported FastAPI app")
except Exception as e:
    print(f"Error importing FastAPI app: {e}")
    # Create a minimal app as fallback
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"message": "Backend running", "error": str(e)}

# Export the app for Vercel
handler = app
