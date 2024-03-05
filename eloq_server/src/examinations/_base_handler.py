from abc import ABC, abstractmethod
from typing import Any, Callable, Mapping, Optional
from fastapi import WebSocket
from pydantic import BaseModel
import json
import logging

import starlette

logger = logging.getLogger(__name__)


class Message(BaseModel):
    action: str
    data: Optional[Any] = None


class BaseHandler(ABC):
    def __init__(self, websocket: WebSocket, callbacks: Mapping[str, Callable[[Message], Optional[Any]]]):
        self.websocket = websocket

        if not self._callbacks_are_valid(callbacks):
            raise ValueError("Invalid callbacks.")

        self.callbacks = callbacks

    async def start(self):
        while True:
            try:
                request = await self._receive()
            except starlette.websockets.WebSocketDisconnect:
                return

            if request.action not in self.cmds:
                logger.error(f"Unknown action {request.action}")
                return

            response = self.callbacks[request.action](
                self._parse_request_body(request))
            if response:
                await self._send(response)

    def _callbacks_are_valid(self, callbacks: Mapping[str, Callable[[Message], None]]) -> bool:
        return set(callbacks.keys()) == self.cmds and all([callable(func) for func in callbacks.values()])

    @property
    def cmds(self):
        return self.CMDS

    async def _send(self, data: Message):
        await self.websocket.send_text(json.dumps(data))

    async def _receive(self) -> Message:
        data = await self.websocket.receive_text()
        return Message.parse_obj(json.loads(data))

    @abstractmethod
    async def _parse_request_body(self, msg: Message) -> Any:
        raise NotImplementedError
