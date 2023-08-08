from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

from .Base import PyObjectId


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    disabled: bool|None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jdoe@example.com",
                "disabled": False,
            }
        }


class UserInRegister(User):
    password1: str
    password2: str


class UserInDB(User):
    hashed_password: str
