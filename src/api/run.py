import uvicorn
import os
from dotenv import load_dotenv
from src.api.app import app

# Load environment variables
load_dotenv()

def main():
    """Run the FastAPI server."""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )

if __name__ == "__main__":
    main()
