# from dataclasses import dataclass
from typing import Union
from pydantic import BaseModel
from ._base_handler import BaseHandler, Message

SPEECH_MAPPING_CMD_START = "START"  # "Mapping" button pressed
SPEECH_MAPPING_CMD_FINISH = "FINISH"  # "<" back arrow pressed
SPEECH_MAPPING_CMD_PAUSE = "PAUSE"  # "paused" or collection ended
SPEECH_MAPPING_CMD_RESUME = "RESUME"  # "unpaused" or "Restart" clicked
SPEECH_MAPPING_CMD_IMAGE = "IMAGE"  # image was shown
SPEECH_MAPPING_CMD_BLINK = "BLINK"  # blink screen was shown
SPEECH_MAPPING_CMD_PATIENT = "PATIENT"

# @dataclass
class ImageData(BaseModel):
    collection_name: str
    image_name: str
    duration: int

    def __repr__(self):
        return "ImageData(collection_name='{}', image_name='{}', duration={})".format(self.collection_name,
                                                                                      self.image_name, self.duration)

# @dataclass
class PatientData(BaseModel):
    name: str
    birthDate: str
    hospital: str
    historyID: str
    hospitalizationDate: str

    def __repr__(self):
        return "PatientData(name ='{}', birthDate='{}', hospital='{}',historyID = '{}',hospitalizationDate = '{}')".format(
            self.name, self.birthDate, self.hospital, self.historyID, self.hospitalizationDate)

# @dataclass
class BlinkData(BaseModel):
    duration: float

    def __repr__(self):
        return "BlinkData(duration={})".format(self.duration)


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
