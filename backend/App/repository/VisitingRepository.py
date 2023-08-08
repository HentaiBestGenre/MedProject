from fastapi.encoders import jsonable_encoder

from App.models import Visit

class VisitingRepository:
    def __init__(self, db) -> None:
        self.collection = db.visits
    
    async def get(self, id: str) -> dict:
        if (visit := await self.collection.find_one({"_id": id})) is not None:
            return visit
    
    async def create(self, visit: Visit) -> dict:
        visit = jsonable_encoder(visit)
        new_task = await self.collection.insert_one(visit)
        new_task = await self.collection.find_one(
            {"_id": new_task.inserted_id}
        )
        return new_task
    
    async def update(self, visiting: dict) -> Visit:
        print("updating visiting")
        update_result = await self.collection.update_one(
            {"_id": visiting['_id']}, {"$set": {
                "entities": visiting["entities"],
                "text": visiting["text"]
            }}
        )
        print("")
        # return Visit(**update_result)

