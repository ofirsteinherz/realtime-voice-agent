"""
Backend service for WebRTC Realtime API.
Entry point - minimal app setup and route registration.
"""
import uvicorn
from fastapi import FastAPI
from routes import router
from config import HOST, PORT

# Create FastAPI app
app = FastAPI()

# Include all routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
