from typing import Type, Union, Any, Callable, Mapping, Optional
from fastapi import Depends, FastAPI, WebSocket, status, Header

import uvicorn

from eloq_server import settings, speech_mapping_handler
from eloq_server import EXAMINATION_HANDLERS, Message, BaseHandler

# from eloq_server.src import examinations

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


def run_server(queue):
    def callback_image(data: speech_mapping_handler.ImageData):
        # print(f"IMAGE event received with data {repr(data)}.")
        queue.put(data)

    def callback_pause(data: None):
        # print("PAUSE event received")
        queue.put("pause")

    def callback_blink(data: speech_mapping_handler.BlinkData):
        queue.put("blink")
        # print(f"BLINK event received with data {repr(data)}.")

    def callback_finish(data: None):
        # print("FINISH event received. Sending all data to the mobile app.")
        queue.put("finish")

    # def callback_connect(data: None):
    #     print("Connection event received")
    #     queue.put("connect")

    def callback_resume(data: None):
        # print("RESUME event received")
        queue.put("resume")

    def callback_start(data: None):
        # print("START event received")
        queue.put("start")

    def callback_patient(data: speech_mapping_handler.PatientData):
        queue.put(data)

    callbacks = {
        speech_mapping_handler.SPEECH_MAPPING_CMD_START: callback_start,
        speech_mapping_handler.SPEECH_MAPPING_CMD_FINISH: callback_finish,
        speech_mapping_handler.SPEECH_MAPPING_CMD_PAUSE: callback_pause,
        speech_mapping_handler.SPEECH_MAPPING_CMD_RESUME: callback_resume,
        speech_mapping_handler.SPEECH_MAPPING_CMD_BLINK: callback_blink,
        speech_mapping_handler.SPEECH_MAPPING_CMD_IMAGE: callback_image,
        speech_mapping_handler.SPEECH_MAPPING_CMD_PATIENT: callback_patient,
    }

    # global app
    app = create_app(callbacks, "speech_mapping")
    # uvicorn.run(__name__ + ":app", port=8000, log_level="info")
    uvicorn.run(app, port=8000, log_level="info")