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


# db init
client = AsyncIOMotorClient(MONGO_DB_URL)
database = client.Whisper


# Loading Models
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


# add routes
app.include_router(auth_router, prefix="/auth")
app.include_router(visiting_router, prefix="/visit")


@app.on_event("startup")
def startup():
    # Setup
    app.state.redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    app.state.visiting_repo = VisitingRepository(database)
    app.state.user_repo = UserRepository(database)
    app.state.connection_manager = WebsocketManager()


@app.on_event('shutdown')
async def shutdown():
    await app.state.redis.close()


def extract_entities(text, ner_model):
    # Extract entities from text
    doc = ner_model(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities


def wright_wav_file(byte_string, sample_width, id):
    # wright wav file with byte string
    # byte_string is byte string
    # sample_width defines the number of bits required to represent the value
    # article about sample_width: https://audioaudit.io/articles/podcast/sample-width
    # id is visiting id 
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
    session: dict|None = Depends(get_session_ws)
    ):
    # websocket that resive byte string of audio
    # url example ws://localhost:8000/ws/qthgnmbcdssgaf/recording 
    # auth is required

    if not session:  # check authentication
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    
    await websocket.accept() 
    visiting = websocket.app.state.connection_manager.add_connection(id, websocket, "mobile") 
    # add websocket into websocket manager and resive patient session
    if not visiting:
        # if session is not in manager check the one in db
        visiting = await websocket.app.state.visiting_repo.get(id)
        # if session is not found raise exeption  
        if not visiting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail='Visiting is not found'
            )
        # if exists and session into manager
        websocket.app.state.connection_manager.add_visit(id, visiting)

    try:
        while True:
            # resive byte string and sample width
            # byte string should be encoded and have type of string 
            # data format is json: {
            #   frames: str,
            #   sample_width: int
            # }
            message: dict = await websocket.receive_json() 
            message['frames'] = base64.b64decode(message['frames'])
            if message['frames'] == b"":
                return
            # wright wav file 
            wright_wav_file(message['frames'], message['sample_width'], id)

            # send data into whisper
            audio = whisper.pad_or_trim(whisper.load_audio(WAVE_OUTPUT_FILENAME.format(id)))
            # resive text
            input_text = whisper.transcribe(model, audio, fp16=False, language='ru')["text"]
            if input_text != " Редактор субтитров А.Семкин Корректор А.Егорова":
                print("RECIVED TEXT: \t", input_text)
                extracted_entities = extract_entities(input_text, nlp)
                res = {"text": input_text, "entities": extracted_entities}
                print("TEXT:\t", res['text'], "\nEntities:\t", res['entities'])
                # send text on desctop
                await websocket.app.state.connection_manager.send_message(res, id, "desctop")
                websocket.app.state.connection_manager.update_visiting(id, res['text'], res['entities'])
    except Exception as e:
        await websocket.close()


@app.websocket("/ws/{id}")
async def main_ws(
    id: str,
    websocket: WebSocket,
    session: dict|None = Depends(get_session_ws)
    ):
    # websocket that connect desctop with server
    # url example ws://localhost:8000/ws/qthgnmbcdssgaf 
    # auth is required

    if not session:  # check authentication
        raise HTTPException(status_code=401, detail="Not authenticated")

    await websocket.accept()
    visiting = websocket.app.state.connection_manager.add_connection(id, websocket, "desctop")
    # add websocket into websocket manager and resive patient session
    if not visiting:
        # if session is not in manager check the one in db
        visiting = await websocket.app.state.visiting_repo.get(id)
        # if session is not found raise exeption  
        if not visiting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail='Visiting is not found'
            )
        # if exists and session into manager
        websocket.app.state.connection_manager.add_visit(id, visiting)

    try:
        while True:
            pass
    except Exception as e:
        # save changes from manager to db when connection is broken
        visiting = websocket.app.state.connection_manager.delete_visiting(id)
        visiting = {**jsonable_encoder(visiting['visiting'])}
        await websocket.app.state.visiting_repo.update(visiting)
        await websocket.close()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)
