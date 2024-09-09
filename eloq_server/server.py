from typing import Type, Union, Any, Callable, Mapping, Optional
from fastapi import Depends, FastAPI, WebSocket, status, Header

import uvicorn

from pydantic import BaseModel
from eloq_server import settings
from eloq_server import Message, BaseHandler
from functools import partial
# from eloq_server.src import examinations


SPEECH_MAPPING_CMD_START = "START"  # "Mapping" button pressed
SPEECH_MAPPING_CMD_FINISH = "FINISH"  # "<" back arrow pressed
SPEECH_MAPPING_CMD_PAUSE = "PAUSE"  # "paused" or collection ended
SPEECH_MAPPING_CMD_RESUME = "RESUME"  # "unpaused" or "Restart" clicked
SPEECH_MAPPING_CMD_IMAGE = "IMAGE"  # image was shown
SPEECH_MAPPING_CMD_BLINK = "BLINK"  # blink screen was shown
SPEECH_MAPPING_CMD_PATIENT = "PATIENT"


class ControlData(BaseModel):
    signal: str

class BlankData(BaseModel):
    signal: str

class BlinkData(BaseModel):
    duration: float

    def __repr__(self):
        return "BlinkData(duration={})".format(self.duration)

class ImageData(BaseModel):
    collection_name: str
    image_name: str
    duration: int

    def __repr__(self):
        return "ImageData(collection_name='{}', image_name='{}', duration={})".format(self.collection_name,
                                                                                      self.image_name, self.duration)
class PatientData(BaseModel):
    name: str
    birthDate: str
    hospital: str
    historyID: str
    hospitalizationDate: str

    def __repr__(self):
        return "PatientData(name ='{}', birthDate='{}', hospital='{}',historyID = '{}',hospitalizationDate = '{}')".format(
            self.name, self.birthDate, self.hospital, self.historyID, self.hospitalizationDate)


class SpeechMappingHandler(BaseHandler):
    CMDS = {
        SPEECH_MAPPING_CMD_START,
        SPEECH_MAPPING_CMD_FINISH,
        SPEECH_MAPPING_CMD_PAUSE,
        SPEECH_MAPPING_CMD_RESUME,
        SPEECH_MAPPING_CMD_IMAGE,
        SPEECH_MAPPING_CMD_BLINK,
        SPEECH_MAPPING_CMD_PATIENT,
    }

    def _parse_request_body(self, msg: Message) -> Union[ImageData, BlinkData, PatientData, None]:
        if msg.action == SPEECH_MAPPING_CMD_IMAGE:
            return ImageData.model_validate(msg.data)

        if msg.action == SPEECH_MAPPING_CMD_BLINK:
            return BlinkData.model_validate(msg.data)

        if msg.action == SPEECH_MAPPING_CMD_PATIENT:
            return PatientData.model_validate(msg.data)

        return None

EXAMINATION_HANDLERS = {
    "speech_mapping": SpeechMappingHandler,
}



def create_app(callbacks: Mapping[str, Callable[[Message], Optional[Any]]], eloq_examination_type: str):
    if eloq_examination_type not in EXAMINATION_HANDLERS.keys():
        raise AttributeError("eloq_examination_type must be one of the: " + " ".join(EXAMINATION_HANDLERS.keys()))

    app = FastAPI()

    async def token(
        websocket: WebSocket,
        eloq_token: Union[str, None] = Header(default=None),
    ):
        if eloq_token is None or eloq_token != settings.TOKEN:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False

        return True

    async def examination(
            websocket: WebSocket,
            examination_type: Union[str, None] = Header(default=None),):
        if examination_type != eloq_examination_type:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        return EXAMINATION_HANDLERS[eloq_examination_type]

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket,
                                 is_token_valid: bool = Depends(token),
                                 examination_handler: Type[BaseHandler] = Depends(examination)):
        if not is_token_valid or examination_handler is None:
            return

        await websocket.accept()
        await examination_handler(websocket, callbacks).start()

    return app



def callback_patient(queue, data: PatientData):
    print("PatientData event received")
    queue.put(data)

def callback_image(queue, data: ImageData):
    print("ImageData event received")
    queue.put(data)

def callback_blink(queue, data: BlinkData):
    print("BLINK event received")
    data = BlankData(signal='BLINK')
    queue.put(data)

def callback_start(queue, data: None):
    print("START event received")
    data = ControlData(signal='START')
    queue.put(data)

def callback_finish(queue, data: None):
    print("FINISH event received.")
    data = ControlData(signal='FINISH')
    queue.put(data)

def callback_pause(queue, data: None):
    print("PAUSE event received")
    data = ControlData(signal='PAUSE')
    queue.put(data)

def callback_resume(queue, data: None):
    print("RESUME event received")
    data = ControlData(signal='RESUME')
    queue.put(data)



def run_server(queue):
    callbacks = {
        SPEECH_MAPPING_CMD_START: partial(callback_start, queue),
        SPEECH_MAPPING_CMD_FINISH: partial(callback_finish, queue),
        SPEECH_MAPPING_CMD_PAUSE: partial(callback_pause, queue),
        SPEECH_MAPPING_CMD_RESUME: partial(callback_resume, queue),
        SPEECH_MAPPING_CMD_BLINK: partial(callback_blink, queue),
        SPEECH_MAPPING_CMD_IMAGE: partial(callback_image, queue),
        SPEECH_MAPPING_CMD_PATIENT: partial(callback_patient, queue),
    }

    # global app
    app = create_app(callbacks, "speech_mapping")
    # uvicorn.run(__name__ + ":app", port=8000, log_level="info")
    uvicorn.run(app, port=8000, log_level="info")