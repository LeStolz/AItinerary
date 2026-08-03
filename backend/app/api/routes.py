from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .auth import get_current_user
import uuid
from app.db.qdrant_db import get_qdrant_client, get_embeddings, COLLECTION_NAME
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from app.db import models, database
from app.api import schemas

router = APIRouter()

# Init DB Tables
models.Base.metadata.create_all(bind=database.engine)

# --- TRAVEL CARDS ---
@router.post("/cards", response_model=schemas.TravelCardOut)
def create_card(card: schemas.TravelCardCreate, db: Session = Depends(database.get_db), user: models.User = Depends(get_current_user)):
    qdrant = get_qdrant_client()
    embeddings = get_embeddings()

    card_id = uuid.uuid4().hex
    text_to_embed = f"{card.title}\n{card.content}"
    vector = embeddings.embed_query(text_to_embed)

    payload = {
        "user_id": user.id,
        "type": card.type,
        "title": card.title,
        "content": card.content
    }

    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=card_id, vector=vector, payload=payload)]
    )

    return {"id": card_id, **payload}

@router.get("/cards", response_model=List[schemas.TravelCardOut])
def read_cards(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), user: models.User = Depends(get_current_user)):
    qdrant = get_qdrant_client()

    results = qdrant.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=user.id))]
        ),
        limit=limit,
        offset=skip
    )[0]

    out = []
    for p in results:
        out.append({"id": p.id, **p.payload})
    return out

@router.delete("/cards/{card_id}")
def delete_card(card_id: str, db: Session = Depends(database.get_db), user: models.User = Depends(get_current_user)):
    qdrant = get_qdrant_client()

    points = qdrant.retrieve(collection_name=COLLECTION_NAME, ids=[card_id])
    if not points or points[0].payload.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Card not found")

    qdrant.delete(collection_name=COLLECTION_NAME, points_selector=[card_id])
    return {"ok": True}

@router.put("/cards/{card_id}", response_model=schemas.TravelCardOut)
def update_card(card_id: str, card: schemas.TravelCardCreate, db: Session = Depends(database.get_db), user: models.User = Depends(get_current_user)):
    qdrant = get_qdrant_client()
    embeddings = get_embeddings()

    points = qdrant.retrieve(collection_name=COLLECTION_NAME, ids=[card_id])
    if not points or points[0].payload.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Card not found")

    text_to_embed = f"{card.title}\n{card.content}"
    vector = embeddings.embed_query(text_to_embed)

    payload = {
        "user_id": user.id,
        "type": card.type,
        "title": card.title,
        "content": card.content
    }

    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=card_id, vector=vector, payload=payload)]
    )

    return {"id": card_id, **payload}

from fastapi import Request
from typing import AsyncGenerator
import json
import asyncio
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.agents.graph import build_graph

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def get_checkpointer():
    db_url = os.getenv("DATABASE_POSTGRES_PRISMA_URL")
    if db_url:
        db_url = db_url.replace("?pgbouncer=true", "")
        db_url = db_url.replace("&pgbouncer=true", "")
        
    if db_url and db_url.startswith("postgres"):
        # Fix for sqlalchemy postgresql:// vs psycopg postgres://
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgres://", 1)
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool
        
        async with AsyncConnectionPool(db_url, kwargs={"prepare_threshold": None}) as pool:
            memory = AsyncPostgresSaver(pool)
            await memory.setup()
            yield memory
    else:
        async with AsyncSqliteSaver.from_conn_string("aitinerary.db") as memory:
            yield memory
# Global graph instance (uncompiled)
workflow = build_graph()

@router.get("/chat/history")
async def get_chat_history(user: models.User = Depends(get_current_user)):
    config = {"configurable": {"thread_id": str(user.id)}}
    messages = []

    async with get_checkpointer() as memory:
        graph = workflow.compile(checkpointer=memory)
        state = await graph.aget_state(config)

        if state and hasattr(state, "values") and "messages" in state.values:
            for msg in state.values["messages"]:
                # The UI only expects the original User message and the final node outputs (which are HumanMessages with names)
                if isinstance(msg, HumanMessage):
                    sender = getattr(msg, "name", None)

                    raw_content = msg.content
                    if isinstance(raw_content, list):
                        text_parts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in raw_content]
                        content_str = "".join(text_parts)
                    else:
                        content_str = str(raw_content)

                    if not sender:
                        messages.append({
                            "sender": "User",
                            "content": content_str,
                            "type": "user"
                        })
                    else:
                        messages.append({
                            "sender": sender,
                            "content": content_str,
                            "type": "agent"
                        })

    return messages

@router.post("/chat")
async def chat_endpoint(request: Request, user: models.User = Depends(get_current_user)):
    data = await request.json()
    message = data.get("message")
    config = {"configurable": {"thread_id": str(user.id)}}

    initial_state = {
        "messages": [HumanMessage(content=message)],
        "next": ""
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        input_state = initial_state
        while True:
            try:
                async with get_checkpointer() as memory:
                    graph = workflow.compile(checkpointer=memory)
                    async for s in graph.astream(input_state, config=config, stream_mode="updates"):
                        for node_name, node_output in s.items():
                            if node_name == "Orchestrator Agent" and "next" in node_output:
                                next_agent = node_output["next"]
                                if next_agent != "FINISH":
                                    yield json.dumps({"active_agent": next_agent})
                            elif node_name in ["Scrapbook Agent", "Logistics", "Booking Agent"]:
                                yield json.dumps({"active_agent": "Orchestrator Agent"})

                            if "messages" in node_output and len(node_output["messages"]) > 0:
                                msg = node_output["messages"][-1]
                                name = getattr(msg, "name", node_name)
                                if not name:
                                    name = node_name

                                raw_content = msg.content
                                if isinstance(raw_content, list):
                                    text_parts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in raw_content]
                                    content_str = "".join(text_parts)
                                else:
                                    content_str = str(raw_content)

                                yield json.dumps({
                                    "sender": name,
                                    "content": content_str
                                })
                                await asyncio.sleep(0.1)
                break
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    yield json.dumps({
                        "sender": "System",
                        "content": "[!] You have hit the Google API Rate Limit (Your key is currently limited to 5 Requests Per Minute). Please wait a minute or upgrade your Google Cloud tier to use multi-agent workflows."
                    })
                    break
                else:
                    yield json.dumps({
                        "sender": "System",
                        "content": f"[!] Error: {msg}"
                    })
                    break

    async def sse_generator():
        async for chunk in event_generator():
            yield {"data": chunk}

    return EventSourceResponse(sse_generator())
