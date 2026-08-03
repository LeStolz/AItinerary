from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.db import models, database

router = APIRouter()
import os

SECRET_KEY = os.getenv("DATABASE_SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

class LoginRequest(BaseModel):
    email: str

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

import os
import resend
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

class MagicLinkRequest(BaseModel):
    email: str

@router.post("/send-magic-link")
def send_magic_link(req: MagicLinkRequest, request: Request):
    expires_delta = timedelta(minutes=15)
    to_encode = {"sub": req.email, "type": "magic_link"}
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    magic_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    verify_url = f"{request.base_url.replace(path='')}/api/auth/verify?token={magic_token}"

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": req.email,
            "subject": "Log in to AItinerary",
            "html": f'<p>Click <a href="{verify_url}">here</a> to securely log in to AItinerary.</p>'
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Magic link sent"}

@router.get("/verify")
def verify_magic_link(token: str, db: Session = Depends(database.get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "magic_link":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired magic link")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Seed default TravelCards into Qdrant
        import json
        import uuid
        from app.db.qdrant_db import get_qdrant_client, get_embeddings, COLLECTION_NAME
        from qdrant_client.http.models import PointStruct

        qdrant = get_qdrant_client()
        embeddings = get_embeddings()

        cards = [
            {
                "type": "preference",
                "title": "My Travel Profile",
                "content": json.dumps({"markdown": "# My Travel Profile\n\n**Budget:** $150/day\n\n**Diet:** Vegetarian\n\n**Pace:** Slow\n\n**Interests:** Art, History, Food"})
            },
            {
                "type": "destination",
                "title": "Dream Trip: Paris",
                "content": json.dumps({"markdown": "# Dream Trip: Paris\n\n**Country:** France\n\nWant to visit the Louvre, Montmartre, and eat lots of croissants!"})
            }
        ]

        points = []
        for c in cards:
            card_id = uuid.uuid4().hex
            text_to_embed = f"{c['title']}\n{c['content']}"
            vector = embeddings.embed_query(text_to_embed)
            payload = {
                "user_id": user.id,
                "type": c["type"],
                "title": c["title"],
                "content": c["content"]
            }
            points.append(PointStruct(id=card_id, vector=vector, payload=payload))

        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    response = RedirectResponse(url=f"{frontend_url}/")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="none",
        secure=True,
        path="/"
    )
    return response
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_me(user: models.User = Depends(get_current_user)):
    return {"user_id": user.id, "email": user.email}
