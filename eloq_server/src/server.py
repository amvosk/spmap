from typing import Type, Union, Any, Callable, Mapping, Optional
from fastapi import Depends, FastAPI, WebSocket, status, Header

from . import settings
from . import examinations


def create_app(callbacks: Mapping[str, Callable[[examinations.Message], Optional[Any]]], eloq_examination_type: str):
    if eloq_examination_type not in examinations.EXAMINATION_HANDLERS.keys():
        raise AttributeError("eloq_examination_type must be one of the: " +
                             " ".join(examinations.EXAMINATION_HANDLERS.keys()))

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

        return examinations.EXAMINATION_HANDLERS[eloq_examination_type]

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket,
                                 is_token_valid: bool = Depends(token),
                                 examination_handler: Type[examinations.BaseHandler] = Depends(examination)):
        if not is_token_valid or examination_handler is None:
            return

        await websocket.accept()
        await examination_handler(websocket, callbacks).start()

    return app
