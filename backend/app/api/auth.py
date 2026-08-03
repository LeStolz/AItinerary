from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.db import models, database
import os
import json
import uuid
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter()

SECRET_KEY = os.getenv("DATABASE_SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

class GoogleAuthRequest(BaseModel):
    credential: str

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

@router.post("/google")
def google_auth(req: GoogleAuthRequest, response: Response, db: Session = Depends(database.get_db)):
    try:
        # Verify the Google JWT token
        idinfo = id_token.verify_oauth2_token(
            req.credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="No email provided by Google")

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # Find or create user
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Seed default TravelCards into Qdrant
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

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="none",
        secure=True,
        path="/"
    )
    return {"message": "Authenticated successfully"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_me(user: models.User = Depends(get_current_user)):
    return {"user_id": user.id, "email": user.email}
