import time, copy
import sched
import multiprocessing
import numpy as np
import copy
import pylsl


class GeneratorLSL:
    def __init__(self, config, em):
        self.config = config
        self.em = em
        # initialize basic configuration
        self.process = None
        # self.queue_input = multiprocessing.Queue()
        # self.queue_output = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()

    # def queue_put(self, input_):
    #     self.queue_input.put(input_)

    # def queue_get(self):
    #     return self.queue_output.get()
    #
    # def queue_empty(self):
    #     return self.queue_output.empty()
    #
    # def queue_size(self):
    #     return self.queue_output.qsize()

    def start(self):
        try:
            self.process = multiprocessing.Process(
                target=generate_sequence,
                args=(copy.deepcopy(self.config), self.stop_event)
            )
            self.process.daemon = True
            self.process.start()
        except:
            self.stop_event.set()
            if self.process.is_alive():
                self.process.join()
            if self.process.is_alive():
                self.process.terminate()

    def stop(self):
        self.stop_event.set()

    def clear(self):
        self.stop_event.set()
        if self.process.is_alive():
            self.process.join()
        if self.process.is_alive():
            self.process.terminate()
        self.stop_event = multiprocessing.Event()
        self.process = None
        # self.queue_input = multiprocessing.Queue()
        # self.queue_output = multiprocessing.Queue()


def generate_sequence(config, stop_event):
    lsl_outlet = _create_lsl(config)
    time2sleep = config.receiver.cache_size / config.receiver.fs
    counter = 0
    while not stop_event.is_set():
        chunk = generate_chunk(config, counter)
        lsl_outlet.push_chunk(chunk)
        time.sleep(time2sleep)
        counter = (counter + 1) % config.receiver.fs

def _create_lsl(config):
    stream_info = pylsl.StreamInfo(
        config.receiver.lsl_stream_name_generator, 'EEG', 69, config.receiver.fs, pylsl.cf_double64, 'myuid88888'
    )
    outlet = pylsl.StreamOutlet(stream_info)
    return outlet

def generate_chunk(config, counter):
    chunk = np.zeros((config.receiver.cache_size, 69))
    chunk_ecog = np.random.normal(size=(config.receiver.cache_size, 64)) * 2 + 2
    # chunk_ecog = np.zeros((config.receiver.cache_size, 64)) + 2
    ratio_ecog = config.receiver.cache_size / config.receiver.fs * 10 * 2 * np.pi
    ratio_ecog_50hz = config.receiver.cache_size / config.receiver.fs * 50 * 2 * np.pi
    ratio_ecog_80hz = config.receiver.cache_size / config.receiver.fs * 80 * 2 * np.pi
    ratio_ecog_5hz = config.receiver.cache_size / config.receiver.fs * 1 * 2 * np.pi
    chunk_ecog += np.sin(np.linspace(counter, (counter + 1), config.receiver.cache_size) * ratio_ecog).reshape(
        config.receiver.cache_size, 1)
    chunk_ecog += np.sin(np.linspace(counter,(counter+1),config.receiver.cache_size)*ratio_ecog_50hz).reshape(
        config.receiver.cache_size, 1) * 2
    chunk_ecog += np.sin(np.linspace(counter,(counter+1),config.receiver.cache_size)*ratio_ecog_80hz).reshape(
        config.receiver.cache_size, 1) * np.sin(np.linspace(counter,(counter+1),config.receiver.cache_size)*ratio_ecog_5hz).reshape(
        config.receiver.cache_size, 1)
    ratio_sound = config.receiver.cache_size / config.receiver.fs
    sinusoid = np.cos(np.linspace(counter,counter+1,config.receiver.cache_size)*ratio_sound)
    chunk_sound = 10 * np.random.normal(size=config.receiver.cache_size) * sinusoid
    chunk[:, 0:64] = chunk_ecog
    chunk[:, config.receiver.sound_channel_index] = chunk_sound
    return chunk


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../core/')
    # sys.path.insert(0, '../config/')
    from config import read_config_file, parse_config
    from event_manager import EventManager

    em = EventManager()


    config_file_default_path = '../config/config_default.ini'
    # config_file_path = '../config/config.ini'
    config_ini = read_config_file(config_file_default_path)
    print(config_ini['patient_info'])
    conf = parse_config(em, config_ini)

    generator = GeneratorLSL(conf, em)
    generator.start()
    for i in range(20):
        time.sleep(0.1)
    generator.stop()
    time.sleep(1)

