from App.models import User, UserInDB
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"])

class UserRepository:
    def __init__(self, db) -> None:
        self.collection = db.users

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password):
        return pwd_context.hash(password)
    
    async def get_user(self, username: str) -> UserInDB:
        if (user := await self.collection.find_one({"username": username})) is not None:
            return UserInDB(**user)
        
    
    async def authenticate_user(self, username: str, password: str):
        user = await self.get_user(username)
        if not user:
            return False
        if not self.verify_password(password, user.hashed_password):
            return False
        return User(**user.dict())
