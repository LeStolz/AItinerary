from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
import json
import asyncio
import os
import re
from app.agents.graph import build_graph
from langgraph.checkpoint.memory import MemorySaver
from app.api import routes
from app.api import auth

app = FastAPI()

frontend_url = os.getenv("FRONTEND_URL")
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(routes.router, prefix="/api")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
