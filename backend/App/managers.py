from fastapi import status, WebSocket
from fastapi.exceptions import HTTPException


class WebsocketManager:
    """Manager for operating websocket connections beetwin desctop and mobile apps"""
    connections = {}

    def add_connection(self, id: str, websocket: WebSocket, connection_type: str):
        if (session := self.connections.get(id)) is not None:
            if session.get(connection_type):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{connection_type} connection is defind for the user"
                )
            session[connection_type] = [websocket]
            return True
        self.connections[id] = {
            connection_type: websocket
        }
        return True
    
    def get_connection(self, id: str, connection_type: str) -> WebSocket:
        if (session := self.connections.get(id)):
            return session.get(connection_type)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session is not defind"
        )
    
    async def send_message(self, message: dict, id: str, connection_type: str):
        ws = self.get_connection(id, connection_type)
        await ws.send_json(message)

    async def send_message_on_desctop(self, message: dict, id: str):
        await self.send_message(message, id, "desctop")