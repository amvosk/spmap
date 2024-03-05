
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

# 123
# from abc import ABC, abstractmethod
# class Recorder:
#     def __init__(self):
#         self.memory = []
#
#     def add(self, chunk):
#         # if len(self.memory) > 0:
#         #     assert self.memory[-1].shape[0] == chunk.shape[0]
#         self.memory.append(chunk)
#
#     def clear(self):
#         self.memory = []
#
#     def save(self, config_recorder):
#         with h5py.File(str(config_recorder.save_path) + '.h5', 'w') as file:
#             if len(self.memory) > 0:
#                 stacked_data = np.concatenate(self.memory, axis=0)
#                 file['raw_data'] = stacked_data[:, config_recorder.channel_index]
#             else:
#                 empty_shape = (0, config_recorder.dataset_width)
#                 file.create_dataset('raw_data', empty_shape)
#
#             file.attrs['fs'] = config_recorder.fs
#             file.attrs['channel_bads'] = np.asarray(config_recorder.channel_bads)
#             file.attrs['channel_names'] = '|'.join(config_recorder.channel_names)

            #
            # file.create_dataset('channel_bads', data=np.asarray(config_recorder.channel_bads))
            # file.create_dataset('channel_names', data=np.asarray(config_recorder.channel_names))
            # file.create_dataset('fs', data=np.array(config_recorder.fs))


class Recorder:
    def __init__(self, config, em):
        # initialize basic configuration
        self.config = config
        self.em = em
        self.process = None
        # self.stop_event = multiprocessing.Event()
        self.queue_input = multiprocessing.Queue()
        self.queue_output = multiprocessing.Queue()

        # self.stimulus = 0

    def queue_put(self, input_):
        self.queue_input.put(input_)

    def queue_get(self):
        return self.queue_output.get()

    def queue_empty(self):
        return self.queue_output.empty()

    def queue_size(self):
        return self.queue_output.qsize()

    def run(self, f):
        try:
            self.process = multiprocessing.Process(
                target=f,
                args=(copy.deepcopy(self.config), self.queue_input, self.queue_output)
            )
            self.process.daemon = True
            self.process.start()

        except Exception:
            print('process stopped')
            if self.process.is_alive():
                self.process.join()
            if self.process.is_alive():
                self.process.terminate()


    def clear(self):
        if self.process.is_alive():
            self.process.join()
        if self.process.is_alive():
            self.process.terminate()
        self.process = None
        self.queue_input = queue.Queue()
        self.queue_output = queue.Queue()


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
        # print('chunk_buffer wrote')
        self.chunk_buffer = []
        tic = time.perf_counter()
        with h5py.File(self.patient_data_amp, 'a') as hdf_file:
            dataset = hdf_file['data']
            new_size = dataset.shape[0] + chunk_buffer.shape[0]
            dataset.resize(new_size, axis=0)
            dataset[-chunk_buffer.shape[0]:] = chunk_buffer
        toc = time.perf_counter()
        print('chunk_buffer wrote, time = ', toc-tic)

    def save_chunk(self, chunk):
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
        self.save_fif(data)
        # with h5py.File(self.patient_data_fif, 'a') as hdf_file:
        #     hdf_file.create_dataset('data', data=data)

        toc = time.perf_counter()
        print('time to rewrite ', toc-tic)


    def save_fif(self, data):
        channel_take = np.concatenate([self.config.receiver.channels, np.asarray([True] * 4)])
        data = data[channel_take]
        ch_names = np.asarray(self.config.processor.channel_names)[channel_take].tolist()
        sfreq = self.config.processor.fs

        ch_types = ['ecog' for _ in range(self.config.receiver.n_channels)] + ['stim' for _ in range(4)]

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



def _run_until_the_end(config, queue_input, queue_output):
    print('hi')
    dataset = None
    stop_flag = 0
    time_cicle = time.perf_counter()
    while True:
        if not queue_input.empty():
            message = queue_input.get(block=False)
            # print("receiver message{}".format(message))
            if message is None:
                continue
            label, data = message
            if label == 'start':
                dataset = Dataset(config)
                # print(data)
            elif label == 'data':
                dataset.save_chunk(data)
                # print(data.shape)
            elif label == 'finish':
                # print(data)
                dataset.save_data()
                stop_flag = 1
        if stop_flag:
            break
        time_sleep = 0.01 + time_cicle - time.perf_counter()
        if time_sleep > 0:
            time.sleep(time_sleep)
    queue_output.put(('save finished in', None))
    print('buy')



