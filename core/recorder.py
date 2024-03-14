
import mne
import sys, time, copy
from os import makedirs
import h5py
#import multiprocessing
import queue
from queue import Empty
#from multiprocessing import Manager,Value,Process
from dataclasses import dataclass

from pathlib import Path

from pylsl import StreamInlet, resolve_byprop
import numpy as np
import multiprocessing
import time
sys.path.insert(0, '../utils/')

import string2ascii


from PyQt6.QtCore import QTimer

import numpy as np
import h5py

class Recorder:
    def __init__(self, config, em):
        # initialize basic configuration
        self.config = config
        self.em = em
        self.process = None
        self.event_finish = multiprocessing.Event()
        self.event_pause = multiprocessing.Event()
        self.queue_input = multiprocessing.Queue()
        self.em.register_handler('experiment.start', self.run)
        self.em.register_handler('experiment.finish', lambda _: self.event_finish.set())
        self.em.register_handler('experiment.pause', lambda _: self.event_pause.set())
        self.em.register_handler('experiment.resume', lambda _: self.event_pause.clear())
        self.em.register_handler('processor.chunk_record', self.record_chunk)


    def record_chunk(self, chunk):
        if self.config.control.recorder_run:
            if (self.process is not None) and self.process.is_alive():
                self.queue_input.put(chunk)

    def run(self, args=None):
        if self.config.control.receiver_run:
            try:
                self.process = multiprocessing.Process(
                    target=_recorder_run,
                    args=(copy.deepcopy(self.config), self.queue_input, self.event_pause, self.event_finish)
                )
                self.process.daemon = True
                self.process.start()
                self.em.trigger('update config.control.recorder_run', True)
            except Exception:
                print('process stopped')
                if self.process.is_alive():
                    self.process.join()
                if self.process.is_alive():
                    self.process.terminate()
                self.em.trigger('update config.control.recorder_run', False)


    def clear(self):
        if self.process.is_alive():
            self.process.join()
        if self.process.is_alive():
            self.process.terminate()
        self.process = None
        while not self.queue_input.empty():
            self.queue_input.get()
        self.event_finish.clear()
        self.event_pause.clear()
        self.em.trigger('update config.control.recorder_run', True)

        # while not self.queue_output.empty():
        #     self.queue_output.get()
        # self.queue_input = multiprocessing.Queue()
        # self.queue_output = multiprocessing.Queue()


class Dataset:
    def __init__(self, config):
        self.config = config
        data_path = Path(self.config.paths.data_path)

        patient_name_ascii = string2ascii.ru2ascii(self.config.patient_info.patient_name)
        patient_dir_name = time.strftime('%y-%m-%d-%H-%M-%S') + '_' + patient_name_ascii
        patient_data_path = data_path / patient_dir_name

        self.patient_data_ini = patient_data_path / '{}.ini'.format(patient_dir_name)
        self.patient_data_amp = patient_data_path / 'amplifier_data.h5'
        self.patient_data_fif = patient_data_path / '{}_ieeg.fif'.format(patient_dir_name)
        makedirs(patient_data_path, exist_ok=True)

        self.config.save(self.patient_data_ini)
        self.chunk_buffer = []
        self.max_buffer_size = 1 * 16
        self.data_shape = (68, 256)

        with h5py.File(self.patient_data_amp, 'a') as hdf_file:
            hdf_file.create_dataset('data', (0, *self.data_shape), maxshape=(None, *self.data_shape), chunks=(1, *self.data_shape))

    def _write_chunk_buffer(self, chunk_buffer):
        self.chunk_buffer = []
        tic = time.perf_counter()
        with h5py.File(self.patient_data_amp, 'a') as hdf_file:
            dataset = hdf_file['data']
            new_size = dataset.shape[0] + chunk_buffer.shape[0]
            dataset.resize(new_size, axis=0)
            dataset[-chunk_buffer.shape[0]:] = chunk_buffer
        toc = time.perf_counter()
        print('chunk_buffer wrote, time = ', toc-tic)

    def save_chunk(self, chunk, pause=False, resume=False):
        control = np.zeros((1, chunk.shape[-1]))
        if pause:
            control[0] = 1
        elif resume:
            control[0] = 2
        chunk = np.concatenate([chunk, control], axis=0)

        self.chunk_buffer.append(chunk)
        if len(self.chunk_buffer) >= self.max_buffer_size:
            chunk_buffer = np.stack(self.chunk_buffer)
            self._write_chunk_buffer(chunk_buffer)
            self.chunk_buffer = []

    def save_data(self):
        if len(self.chunk_buffer) > 0:
            chunk_buffer = np.zeros((0, *self.data_shape))
            if len(self.chunk_buffer) == 1:
                chunk_buffer = np.expand_dims(self.chunk_buffer[0], axis=0)
            elif len(self.chunk_buffer) > 1:
                chunk_buffer = np.stack(self.chunk_buffer)
            self._write_chunk_buffer(chunk_buffer)
            self.chunk_buffer = []
        tic = time.perf_counter()
        with h5py.File(self.patient_data_amp, 'r') as hdf_file:
            data = hdf_file['data'][()]
        data = np.transpose(data, (1, 0, 2)).reshape((self.data_shape[0], -1))
        if data.shape[-1] > 0:
            self.save_fif(data)
        toc = time.perf_counter()
        print('time to rewrite ', toc-tic)


    def save_fif(self, data):
        channel_take = np.concatenate([self.config.processor.channels, np.asarray([True] * 4)])
        data = data[channel_take]
        ch_names = self.config.processor.channel_names + ['control']
        sfreq = self.config.processor.fs

        ch_types = ['ecog' for _ in range(self.config.processor.n_channels)] + ['stim' for _ in range(4)]

        info = mne.create_info(
            ch_names=ch_names,
            sfreq=sfreq,
            ch_types=ch_types
        )
        raw = mne.io.RawArray(data, info, verbose=False)

        for ch_name, bad in zip(info.ch_names[:-4], self.config.processor.channels_bad):
            if bad:
                raw.info['bads'].append(ch_name)
        raw.save(self.patient_data_fif, overwrite=True, verbose=False)



def _recorder_run(config, queue_input, event_pause, event_finish):
    dataset = Dataset(config)
    pause_on = False
    time_cicle = time.perf_counter()
    while True:
        if event_finish.is_set():
            dataset.save_data()
            break

        if not queue_input.empty():
            message = queue_input.get(block=False)

            if event_pause.is_set() and pause_on:
                continue
            elif (not event_pause.is_set()) and pause_on:
                dataset.save_chunk(message, resume=True)
                pause_on = False
            elif event_pause.is_set() and (not pause_on):
                dataset.save_chunk(message, pause=True)
                pause_on = True
            elif (not event_pause.is_set()) and (not pause_on):
                dataset.save_chunk(message)

        time_sleep = 0.01 + time_cicle - time.perf_counter()
        if time_sleep > 0:
            time.sleep(time_sleep)

    event_pause.clear()
    event_finish.clear()




