from fastapi import status, WebSocket
from fastapi.exceptions import HTTPException

import spacy
from spacy.training import Example
import pickle


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


class NERManager:
    """
    Manager for operating websocket connections beetwin desctop and mobile apps
    Contains info about active sessions
    """
    connections = {}

    def __init__(self, NER_PATH, MATCHER_PATH) -> None:
        self.NER_PATH = NER_PATH
        self.MATCHER_PATH = MATCHER_PATH
        self.nlp = spacy.load(NER_PATH)
        self.matcher = pickle.load(open(MATCHER_PATH, 'rb'))


    def extract_entities(self, text):
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            print(self.nlp.vocab.strings[match_id], doc[start:end])
            
            
        entities = [(
            ent.text, ent.label_
        ) for ent in doc.ents] + [(
            doc[start:end].text, self.nlp.vocab.strings[match_id]
        ) for match_id, start, end in matches]
        return entities
    

    def add_matcher_patern(patern, lable):
        pass

    
    def fine_tuning(self, train_data: list, iterations = 5):
        """
        Take data in format: [
        (
            'text',
            {'entities': [
                (start_index, end_index, 'lable'), 
                (start_index, end_index, 'lable'), 
                (start_index, end_index, 'lable')
            ]}
        )
        ]
        """

        ner = self.nlp.get_pipe("ner")

        for _, annotations in train_data:
            for ent in annotations.get("entities"):
                ner.add_label(ent[2])

        other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        with self.nlp.disable_pipes(*other_pipes):
            optimizer = self.nlp.begin_training()
            for _ in range(iterations):
                losses = {}
                examples = [
                    Example.from_dict(self.nlp.make_doc(text), annotations) 
                    for text, annotations in train_data
                ]
                self.nlp.update(examples, drop=0.5, losses=losses)
            print(losses)
        return ner
    

    def save_ner(self, path):
        self.nlp.to_disk(path)
