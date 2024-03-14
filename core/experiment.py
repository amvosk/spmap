
import time, copy
import multiprocessing
import numpy as np
from stimulus import Stimulus
from PyQt6 import QtCore

import sys
sys.path.insert(0, '../eloq_server')
# sys.path.insert(0, '../core')
# from src import _debug_example
from server import run_server
import uvicorn
import queue
import multiprocessing

class Experiment:
    def __init__(self, config, em, qt):
        # initialize basic configuration
        self.config = config
        self.em = em
        self.process = None
        self.queue_input = multiprocessing.Queue()
        # self.connection_status = False

        self.timer = QtCore.QTimer(qt)
        self.timer.timeout.connect(lambda : self.parse_message(self.queue_input))
        self.timer.start(1)

    def parse_message(self, queue):
        if queue.empty():
            return
        data = queue.get(block=False)
        if data.__class__.__name__ == 'PatientData':
            # for key, value in vars(data).items():
            self.em.trigger('update config.patient_info.patient_name', data.name)
            self.em.trigger('update config.patient_info.patient_date', data.birthDate)
            self.em.trigger('update config.patient_info.patient_hospital', data.hospital)
            self.em.trigger('update config.patient_info.patient_history_id', data.historyID)
            self.em.trigger('update config.patient_info.patient_hospitalization_date', data.hospitalizationDate)
        elif data.__class__.__name__ == 'ControlData':
            if data.signal.lower() == 'start':
                self.em.trigger('experiment.start')
            elif data.signal.lower() == 'finish':
                self.em.trigger('experiment.finish')
            elif data.signal.lower() == 'pause':
                self.em.trigger('experiment.pause')
            elif data.signal.lower() == 'resume':
                self.em.trigger('experiment.resume')
            # self.em.trigger('update config.control.receiver_run', True)
            # self.em.trigger('experiment.transition', data.signal.lower())
        elif data.__class__.__name__ == 'ImageData':
            self.em.trigger('experiment.stimulus_image', data.image_name)
        elif data.__class__.__name__ == 'BlankData':
            self.em.trigger('experiment.blank')
        else:
            print('experiment failed me')

    # if self.experiment_start:
    #     self.em.trigger('recorder.start')
    # elif self.experiment_finish:
    #     self.em.trigger('recorder.finish')
    # elif self.experiment_pause:
    #     self.em.trigger('recorder.pause')
    # elif self.experiment_resume:
    #     self.em.trigger('recorder.unpause')


    # def parse_control(self, data):
    #     if data == 'start':
    #         self.experiment_start = True
    #         self.experiment_finish = False
    #     elif data == 'finish':
    #         self.experiment_start = False
    #         self.experiment_finish = True
    #     elif data == 'pause':
    #         self.experiment_pause = True
    #         self.experiment_resume = False
    #     elif data == 'resume':
    #         self.experiment_pause = False
    #         self.experiment_resume = True





    def start(self):
        try:
            self.queue_input = multiprocessing.Queue()
            self.process = multiprocessing.Process(
                target=run_server,
                args=(self.queue_input,)
            )
            self.process.daemon = True
            self.process.start()
        except Exception as exception:
            print(exception)
            print('cant start experiment')
            if self.process.is_alive():
                self.process.join()
            if self.process.is_alive():
                self.process.terminate()

    def clear(self):
        # if self.receiver_process.is_alive():
        #     self.receiver_process.join()
        if self.process.is_alive():
            self.process.terminate()
        self.process = None
        self.queue_input = multiprocessing.Queue()

















