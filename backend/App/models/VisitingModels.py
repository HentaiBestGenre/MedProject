from pydantic import BaseModel, Field
from bson import ObjectId

from .Base import PyObjectId


class Visit(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    entities: list = list()
    text: list = list()

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "entities": [],
                "text": []
            }
        }
