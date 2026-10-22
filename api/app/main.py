"""Main FastAPI entry point for VibeBreaker backend."""
import os
import sys

# Add the api/app directory to path FIRST so all subsequent imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
# Explicitly look for .env in current directory and parent directories
_current_dir = os.path.dirname(os.path.abspath(__file__))
_api_env = os.path.abspath(os.path.join(_current_dir, "..", ".env"))
if os.path.exists(_api_env):
    load_dotenv(dotenv_path=_api_env)
else:
    load_dotenv()

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db.models import init_db
from app.routes import register_routes
from app.services.agent_loop import AgentLoop

app = FastAPI(title="VibeBreaker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
init_db()

@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "VibeBreaker API"}

# Register routes
register_routes(app)