
import time, copy
import multiprocessing
import numpy as np
from stimulus import Stimulus

import sys
sys.path.insert(0, '../eloq_server')
from src import _debug_example
import uvicorn
import queue 
import multiprocessing

class Experiment:
    def __init__(self, config, em, config_local):
        # initialize basic configuration
        self.config = config
        self.em = em
        self.config_local = config_local
        self.process = None
        self.queue_input = multiprocessing.Queue()
        self.queue_output = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()
        self.pause_event = multiprocessing.Event()
        self.connection_status = False

        self.em.register_handler('experiment.start', self.start)
        self.em.register_handler('experiment.stop', self.stop)
        self.em.register_handler('experiment.pause', self.pause)
        self.em.register_handler('experiment.unpause', self.unpause)

    def queue_put(self, input_):
        self.queue_input.put(input_)

    def queue_get(self):
        return self.queue_output.get()

    def queue_empty(self):
        return self.queue_output.empty()

    def start(self, args):
        try:
            self.queue_input = multiprocessing.Queue()
            self.queue_output = multiprocessing.Queue()
            self.stop_event = multiprocessing.Event()
            self.pause_event = multiprocessing.Event()
            self.process = multiprocessing.Process(
                target=run_experiment,
                args=(
                    copy.deepcopy(self.config),
                    np.copy(self.config_local.splits_values[self.config_local.split]),
                    self.queue_output,
                    self.stop_event,
                    self.pause_event)
            )
            self.process.daemon = True
            self.process.start()
        except Exception as e:
            print(e)
            print('cant start experiment')
    #         if self.receiver_process.is_alive():
    #             self.receiver_process.join()
    #         if self.receiver_process.is_alive():
    #             self.receiver_process.terminate()

    def stop(self, args):
        self.stop_event.set()

    def pause(self, args):
        self.pause_event.set()

    def unpause(self, args):
        self.pause_event.clear()

# def run_experiment(config, split, queue_output, stop_event, pause_event):
#     # picture_path = config.paths.app_path
#     time.sleep(1)
#     for value in split:
#         if not stop_event.is_set():
#             queue_output.put(value)
#             time.sleep(3)
#             while pause_event.is_set():
#                 time.sleep(1)
#         else:
#             break

def run_experiment(config, split, queue_output, stop_event, pause_event):
    _debug_example.run_server(queue_output)
