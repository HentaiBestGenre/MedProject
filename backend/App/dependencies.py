from fastapi import Request, WebSocket

import json


async def get_session(request: Request):
    session_id = request.session.get("session_id")
    if not session_id:
        return {}
    session_data = await request.app.state.redis.get(session_id)
    if not session_data:
        return {}
    return json.loads(session_data)


async def get_session_ws(websocket: WebSocket):
    session_id = websocket.session.get("session_id")
    if not session_id:
        return {}
    session_data = await websocket.app.state.redis.get(session_id)
    if not session_data:
        return {}
    return json.loads(session_data)


async def get_redis(request: Request):
    return request.app.state.redis


async def get_redis_ws(websocket: WebSocket):
    return websocket.app.state.redis

async def get_user_repo(request: Request):
    return request.app.state.user_repo

async def get_visiting_repo(request: Request):
    return request.app.state.visiting_repo
