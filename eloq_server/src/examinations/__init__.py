from .speech_mapping_handler import SpeechMappingHandler
from ._base_handler import BaseHandler, Message


EXAMINATION_HANDLERS = {
    "speech_mapping": SpeechMappingHandler,
}


__all__ = [
    'EXAMINATION_HANDLERS',
    'BaseHandler',
    'Message',
]
