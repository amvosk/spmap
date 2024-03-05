from .server import create_app
from .examinations import speech_mapping_handler
import logging
import uvicorn 
#logger = logging.getLogger(__name__)

def _callback_with_response(data: None):
    return [1, 2, 3]  # can be anything


def _callback_without_response(data: None) -> None:
    return None


def callback_start(data: None) -> None:
    print("START event received")
    return None


def callback_finish(data: None):
    print("FINISH event received. Sending all data to the mobile app.")
    result_data = {"event": "RESULT", "data": [1, 2, 3]}
    return result_data


def callback_pause(data: None) -> None:
    print("PAUSE event received")
    return None


def callback_resume(data: None) -> None:
    print("RESUME event received")
    return None


def callback_blink(data: speech_mapping_handler.BlinkData):
    print(f"BLINK event received with data {repr(data)}.")
    return None


def callback_image(data: speech_mapping_handler.ImageData):
    print(f"IMAGE event received with data {repr(data)}.")
    queue.put(data)
    #return repr(data)



callbacks = {
    speech_mapping_handler.SPEECH_MAPPING_CMD_START: callback_start,
    speech_mapping_handler.SPEECH_MAPPING_CMD_FINISH: callback_finish,
    speech_mapping_handler.SPEECH_MAPPING_CMD_PAUSE: callback_pause,
    speech_mapping_handler.SPEECH_MAPPING_CMD_RESUME: callback_resume,
    speech_mapping_handler.SPEECH_MAPPING_CMD_BLINK: callback_blink,
    speech_mapping_handler.SPEECH_MAPPING_CMD_IMAGE: callback_image,
}

#app = create_app(callbacks, "speech_mapping")

app = None    
def run_server(queue):
    global app
    
    def callback_image(data: speech_mapping_handler.ImageData):
        #print(f"IMAGE event received with data {repr(data)}.")
        queue.put(data)
        #time.sleep(data.duration)
    
    def callback_pause(data: None) -> None:
    	print("PAUSE event received")
    	queue.put("pause")
    	return None
       
    def callback_blink(data: speech_mapping_handler.BlinkData):
    	queue.put("blink")
    	print(f"BLINK event received with data {repr(data)}.")
    	return None
    	
    def callback_finish(data: None):
        print("FINISH event received. Sending all data to the mobile app.")
        queue.put("finish")	
    
    def callback_connect(data: None):
        print("Connection event received")
        queue.put("connect")
    
    def callback_start(data: None) -> None:
        print("START event received")
        queue.put("start")
    

    class ConnectionOpenHandler(logging.Handler):
        def emit(self, record):
            print("New connection opened!")
            log_message = self.format(record)
            if "connection open" in log_message:
                print("New connection opened!")
                # Здесь вы можете добавить свою логику для обработки события

    # Создание и настройка обработчика для перехвата событий "connection open"
    connection_open_handler = ConnectionOpenHandler()

    # Добавление обработчика к корневому логгеру
    logging.root.addHandler(connection_open_handler)

    callbacks = {
    speech_mapping_handler.SPEECH_MAPPING_CMD_START: callback_start,
    speech_mapping_handler.SPEECH_MAPPING_CMD_FINISH: callback_finish,
    speech_mapping_handler.SPEECH_MAPPING_CMD_PAUSE: callback_pause,
    speech_mapping_handler.SPEECH_MAPPING_CMD_RESUME: callback_resume,
    speech_mapping_handler.SPEECH_MAPPING_CMD_BLINK: callback_blink,
    speech_mapping_handler.SPEECH_MAPPING_CMD_IMAGE: callback_image,
    }
    
    app = create_app(callbacks, "speech_mapping")	
    uvicorn.run(__name__ + ":app", port=8000, log_level="info")
   
