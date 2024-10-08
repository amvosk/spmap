import time
import sched
import multiprocessing
import numpy as np
import copy
import pylsl
import h5py

from eloq_server import callback_patient, callback_image, callback_pause, callback_blink, callback_finish, callback_resume, callback_start
from eloq_server import PatientData, ImageData, ControlData, BlankData


class RecordLSL:
    def __init__(self, config, em):
        self.config = config
        self.em = em
        # initialize basic configuration
        self.process = None
        self.stop_event = multiprocessing.Event()
        self.queue = None

    def start(self):
        try:
            self.process = multiprocessing.Process(
                target=generate_sequence,
                args=(copy.deepcopy(self.config), self.stop_event, self.queue)
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
        self.queue_out = None
        self.process = None


def generate_sequence(config, stop_event, queue):
    file_path = '../resource/data/experiment_data.h5'
    with h5py.File(file_path, "r") as file:
        data = (file['raw_data'][()]).astype('float64').T

    n_chunks = data.shape[-1] // config.receiver.cache_size
    data = data[..., :n_chunks * config.receiver.cache_size]

    lsl_outlet = _create_lsl(config)
    time2sleep = config.receiver.cache_size / config.receiver.fs
    counter = 0
    counter_pictures = 1

    while not stop_event.is_set():
        chunk = generate_chunk(config, data, counter)

        if len(np.where(chunk[...,70] < 0)[0] > 0):
            callback_blink(queue, None)
        elif len(np.where(chunk[...,70] > 0)[0] > 0):
            image_name = f'assets/collections/object_l1/{counter_pictures % 51}.jpg'
            counter_pictures += 1
            image_data = ImageData(collection_name='object_l1', image_name=image_name, duration=1.0)
            callback_image(queue, image_data)

        lsl_outlet.push_chunk(chunk)
        time.sleep(time2sleep)
        counter = (counter + 1) % n_chunks



def _create_lsl(config):
    stream_info = pylsl.StreamInfo(
        config.receiver.lsl_stream_name_record, 'EEG', 71, config.receiver.fs, pylsl.cf_double64, 'myuid88888'
    )

    # outlet = pylsl.StreamOutlet(stream_info)
    outlet = pylsl.stream_outlet(stream_info, chunk_size=config.receiver.cache_size, max_buffered=3)
    return outlet

def generate_chunk(config, data, counter):
    chunk = data[...,counter * config.receiver.cache_size: (counter+1) * config.receiver.cache_size]
    chunk = chunk.T
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
    conf = parse_config(em, config_ini)

    generator = RecordLSL(conf, em)
    generator.start()
    for i in range(50):
        time.sleep(0.1)
    generator.stop()
    time.sleep(1)
