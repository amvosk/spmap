# -*- coding: utf-8 -*-
"""
Created on Sat Feb 29 13:31:28 2020

@author: AlexVosk
"""

import time, copy
#import multiprocessing
import queue
from queue import Empty
#from multiprocessing import Manager,Value,Process
from dataclasses import dataclass

from pylsl import StreamInlet, resolve_byprop
import numpy as np
import multiprocessing

@dataclass
class RecorderFlags:
    # connection_state: int
    # experiment_state: int
    control_index: int
    stimulus_index: int
    cache_index: int


class NoStreamError(ConnectionError):
    pass


class EmptyStreamError(ConnectionError):
    pass


def _connect_lsl(config_receiver):
    try:
        streams = resolve_byprop('name', config_receiver.lsl_stream_name, timeout=1)
        # if len(streams) == 0 or len(streams) >= 2:
        print('Found {} streams with name {}'.format(len(streams), config_receiver.lsl_stream_name))
    except TimeoutError:
        raise NoStreamError(
            'No lsl streams with name {} detected'.format(config_receiver.lsl_stream_name)) from None
    for i, stream in enumerate(streams):
        try:
            inlet = StreamInlet(stream, config_receiver.fs)
            _, timestamp = inlet.pull_sample(timeout=1)
            if timestamp:
                return inlet
        except TimeoutError:
            print('{} out of {} lsl streams is empty'.format(i + 1, len(streams)))
    raise EmptyStreamError(
        'Found {} streams, all streams with name {} are empty'.format(len(streams),
                                                                      config_receiver.lsl_stream_name)) from None


def resolve_queue_input(flags, receiver_queue_input_):
    try: 
        value = receiver_queue_input_.get(block=False)
        print("recieved value", value)
        if(value == 'blink' or value == 'pause' or value == 'finish'):
            #flags = self.queue_input.get()
            print(0)
            return 0 
        else: 
            print(1)
            return 1

    except Empty:
        return flags.stimulus_index


def _connect(config_receiver, queue_input, queue_output, stop_event):
    try:
        inlet = _connect_lsl(config_receiver)
    except ConnectionError as exc:
        print(exc)
        stop_event.set()
        inlet = None

    flags = RecorderFlags(
        # connection_state=1,
        # experiment_state=0,
        control_index=0,
        stimulus_index=0,
        cache_index=0,
    )

    # flags = resolve_queue_input(flags, queue_input)
    cache = np.zeros((config_receiver.cache_size, config_receiver.cache_width))
    while not stop_event.is_set():

        #flags = resolve_queue_input(flags, queue_input)
        flags.stimulus_index = resolve_queue_input(flags, queue_input)
        #print(flags)
        # pull sample and check, is it successful
        sample, timestamp = inlet.pull_sample(timeout=1)
        if timestamp is None:
            message = ('lost connection, data saved', True)
            queue_output.put(message)
            inlet.close_stream()
            return
        # if timestamp exists, add sample to the cache
        else:
            sample = np.asarray(sample)
            big_sample = np.zeros(config_receiver.cache_width)
            # add sEEG data
            big_sample[0:config_receiver.n_channels_max] = sample[:config_receiver.n_channels_max]
            # add sound data
            big_sample[config_receiver.sound_channel_index] = sample[config_receiver.sound_channel_index]
            # add timestamp
            big_sample[config_receiver.timestamp_channel_index] = time.perf_counter()
            # add control_index
            big_sample[config_receiver.control_channel_index] = flags.control_index
            # add stimulus_index
            big_sample[config_receiver.stimulus_channel_index] = flags.stimulus_index
            cache[flags.cache_index] = big_sample
            flags.cache_index += 1

            #flags.control_index = 0
            #flags.stimulus_index = 0
            
        if flags.cache_index == config_receiver.cache_size:
            queue_output.put(('chunk', np.copy(cache)))
            cache = np.zeros((config_receiver.cache_size, config_receiver.cache_width))
            flags.cache_index = 0

        if stop_event.is_set() and flags.cache_index > 0:
            queue_output.put(('chunk', np.copy(cache[:flags.cache_index])))
    if inlet is not None:
        inlet.close_stream()



class Receiver:
    def __init__(self, config, em):
        # initialize basic configuration
        self.config = config
        self.em = em
        self.receiver_process = None
        self.stop_event = multiprocessing.Event()
        self.queue_input = multiprocessing.Queue()
        self.queue_output = multiprocessing.Queue()

        self.stimulus = 0

    def queue_put(self, input_):
        self.queue_input.put(input_)

    def queue_get(self):
        return self.queue_output.get()

    def queue_empty(self):
        return self.queue_output.empty()

    def queue_size(self):
        return self.queue_output.qsize()

    
    def stimulus_check(self, queue): #queue из experiment --> _debug_example
        try: 
            value = queue.get(block=False)
            if(value == 'blink' or value == 'pause' or value == 'finish'):
                #flags = self.queue_input.get()
                self.stimulus = 0
            else: 
                self.stimulus = 1
        except Empty:
            pass

    def connect(self):
        try:
            self.receiver_process = multiprocessing.Process(
                target=_connect,
                args=(copy.deepcopy(self.config.receiver), self.queue_input, self.queue_output, self.stop_event)
            )
            #self.receiver_process.daemon = True
            self.receiver_process.start()
        except ConnectionError:
            print('connection error')
            if self.receiver_process.is_alive():
                self.receiver_process.join()
            if self.receiver_process.is_alive():
                self.receiver_process.terminate()

    def disconnect(self):
        self.stop_event.set()
        # try:
        #     self.queue_put({'connection_state': 0})
        # except AttributeError as exc:
        #     print('No process available to disconnect')
    #
    # def stop(self):
    #     self.stop_event.set()

    def clear(self):
        self.stop_event.set()
        # if self.receiver_process.is_alive():
        #     self.receiver_process.join()
        time.sleep(0.005)
        if self.receiver_process.is_alive():
            self.receiver_process.terminate()
        self.receiver_process = None
        self.stop_event = multiprocessing.Event()
        self.queue_input = multiprocessing.Queue()
        self.queue_output = multiprocessing.Queue()


if __name__ == '__main__':
    pass
#how to block buttons and feilds from change while one buttom is pressed?