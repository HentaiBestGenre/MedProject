from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.requests import Request
from aioredis import Redis
import secrets
import json
from fastapi.encoders import jsonable_encoder

from App.dependencies import get_redis, get_session
router = APIRouter()


@router.post("/login")
async def login(username: str, password: str, request: Request, redis: Redis = Depends(get_redis)):
    user = await request.app.state.user_repo.authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authentiticate": "Bearer"}
        )
    user_data = jsonable_encoder(user)
    session_id = secrets.token_hex(32)
    session_id = f"session:{session_id}"
    await redis.set(session_id, json.dumps({**user_data, "visitings": {}}))
    request.session["session_id"] = session_id
    return {"message": "Login successful"}


@router.get("/profile")
async def get_profile(session: dict = Depends(get_session)):
    if session:
        return session
    raise HTTPException(status_code=401, detail="Not authenticated")


@router.delete("/logout")
async def logout(request: Request, redis: Redis = Depends(get_redis)):
    session_id = request.session.get("session_id")
    if session_id:
        await redis.delete(session_id)
    request.session.clear()
    return {"message": "Logged out"}