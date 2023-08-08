from fastapi import FastAPI, Depends, status, WebSocket
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import aioredis
from aioredis import Redis
import json
import spacy
import wave
import whisper
import base64

from App.routers import auth_router, visiting_router
from App.repository import VisitingRepository, UserRepository
from App.dependencies import get_redis_ws, get_session_ws
from App.managers import WebsocketManager
from config import *


# managers
# connection types: desctop, mobile



# db init
client = AsyncIOMotorClient(MONGO_DB_URL)
database = client.Whisper


# NN Models
nlp = spacy.load(NER_PATH)
model = whisper.load_model("base")


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


app.include_router(auth_router, prefix="/auth")
app.include_router(visiting_router, prefix="/visit")


@app.on_event("startup")
def startup():
    app.state.redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    app.state.visiting_repo = VisitingRepository(database)
    app.state.user_repo = UserRepository(database)
    app.state.connection_manager = WebsocketManager()


@app.on_event('shutdown')
async def shutdown():
    await app.state.redis.close()
id

def extract_entities(text, ner_model):
    doc = ner_model(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities


def wright_wav_file(byte_string, sample_width, id):
    try:
        waveFile = wave.open(WAVE_OUTPUT_FILENAME.format(id), 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(sample_width)
        waveFile.setframerate(RATE)
        waveFile.writeframes(byte_string)
        waveFile.close()
        return True
    except Exception as e:
        print(e)
        return False


@app.websocket("/ws/{id}/recording")
async def recording_ws(
    id: str,
    websocket: WebSocket,
    session: dict|None = Depends(get_session_ws),
    redis: Redis = Depends(get_redis_ws)
    ):
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session_id = websocket.session.get("session_id")
    
    
    visiting = session['visitings'].get(id)
    if visiting is None:
        visiting = await websocket.app.state.visiting_repo.get(id)
        if not visiting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail='Session is not found'
            )
        session['visitings'][id] = visiting
        await redis.set(session_id, json.dumps(session))
    
    await websocket.accept()
    websocket.app.state.connection_manager.add_connection(id, websocket, "mobile")
    try:
        while True:
            message: dict = await websocket.receive_json()
            message['frames'] = base64.b64decode(message['frames'])
            if message['frames'] == b"":
                return
            wright_wav_file(message['frames'], message['sample_width'], id)

            audio = whisper.pad_or_trim(whisper.load_audio(WAVE_OUTPUT_FILENAME.format(id)))
            input_text = whisper.transcribe(model, audio, fp16=False, language='ru')["text"]
            if input_text != " Редактор субтитров А.Семкин Корректор А.Егорова":
                print("RECIVED TEXT: \t", input_text)
                extracted_entities = extract_entities(input_text, nlp)
                res = {"text": input_text, "entities": extracted_entities}
                print("TEXT:\t", res['text'], "\nEntities:\t", res['entities'])
                await websocket.app.state.connection_manager.send_message(res, id, "desctop")
                session['visitings'][id]['text'].append(res['text'])
                session['visitings'][id]['entities'].append(res['entities'])
                await redis.set(session_id, json.dumps(session))
    except Exception as e:
        await websocket.close()


@app.websocket("/ws/{id}")
async def main_ws(
    id: str,
    websocket: WebSocket,
    session: dict|None = Depends(get_session_ws),
    redis: Redis = Depends(get_redis_ws)
    ):

    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session_id = websocket.session.get("session_id")

    visiting = await websocket.app.state.visiting_repo.get(id)
    if not visiting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail='Session is not found'
        )
    
    await websocket.accept()
    websocket.app.state.connection_manager.add_connection(id, websocket, "desctop")
    try:
        while True:
            received_data = await websocket.receive_json()
    except Exception as e:
        session = json.loads(await redis.get(session_id))
        data = session.get("visitings").pop(id)
        visiting = {**jsonable_encoder(visiting), "entities": data['entities'], "text": data['text']}
        await websocket.app.state.visiting_repo.update(visiting)
        await redis.set(session_id, json.dumps(session))
        await websocket.close()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)
