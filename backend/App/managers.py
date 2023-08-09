from fastapi import status, WebSocket
from fastapi.exceptions import HTTPException


class WebsocketManager:
    """
    Manager for operating websocket connections beetwin desctop and mobile apps
    Contains info about active sessions
    """
    connections = {}

    def add_connection(self, id: str, websocket: WebSocket, connection_type: str):
        # add websocket into connection pull for let them communicate
        if (session := self.connections.get(id)) is not None:
            if session.get(connection_type):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{connection_type} connection is defind for the user"
                )
            session[connection_type] = [websocket]
            return session['visiting']
        self.connections[id] = {
            connection_type: websocket,
            "visiting": None
        }
        return None
    
    def get_connection(self, id: str, connection_type: str) -> WebSocket:
        # get websocket connection
        if (session := self.connections.get(id)):
            return session.get(connection_type)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session is not defind"
        )
    
    def add_visit(self, id: str, visit: dict) -> WebSocket:
        # set visiting 
        if (session := self.connections.get(id)):
            session['visiting'] = visit
            return 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session is not defind"
        )
    
    def get_visit(self, id: str) -> WebSocket:
        # return visiting
        if (session := self.connections.get(id)):
            return session['visiting']
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session is not defind"
        )
    
    def update_visiting(self, id: str, text: str, entities: dict) -> WebSocket:
        # add transcribed text and entities
        if (session := self.connections.get(id)):
            session['visiting']['text'].append(text)
            session['visiting']['entities'].append(entities)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session is not defind"
        )
    
    def delete_visiting(self, id: str) -> WebSocket:
        # delete patient session, is trigered after breaking pc->server connection
        if (session := self.connections.get(id)):
            self.connections.remove(session)
            return session
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session is not defind"
        )
    
    async def send_message(self, message: dict, id: str, connection_type: str):
        # send message on a client side
        ws = self.get_connection(id, connection_type)
        await ws.send_json(message)

    async def send_message_on_desctop(self, message: dict, id: str):
        # send message from mobile client side to desctop
        await self.send_message(message, id, "desctop")