from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import spacy
import whisper

from App.repository import UserRepository
from App.models import Visit
from App.dependencies import get_visiting_repo


WAVE_OUTPUT_FILENAME = "/home/vadim/Projects/Whisper_app/App/data/{}.wav"
CHANNELS = 1
RATE = 44100
visits = []

nlp = spacy.load("/home/vadim/Projects/Whisper_app/App/neural_networks/NER")
model = whisper.load_model("base")


# Dependencies
def get_redis(request: Request):
    return request.app.state.redis


router = APIRouter()
data = []


@router.get("/{id}")
async def get_profile(id: str, visiting_repo = Depends(get_visiting_repo)):
    visit = await visiting_repo.get(id)
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content=jsonable_encoder(visit)
    )



@router.post("/")
async def create(visit: Visit, visiting_repo: UserRepository = Depends(get_visiting_repo)):
    visit = await visiting_repo.create(visit)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, 
        content=jsonable_encoder(visit)
    )
