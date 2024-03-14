import sys, os, time
import numpy as np
import h5py
import mne

sys.path.insert(0, '../core/')
sys.path.insert(0, '../config/')
from event_manager import EventManager
from config import read_config_file, parse_config
from recorder import Recorder, _recorder_run

if __name__ == '__main__':
    config_file_path = '../config/config_default.ini'
    config_ini = read_config_file(config_file_path)
    em = EventManager()
    config = parse_config(em, config_ini)

    recdr = Recorder(config, em)
    recdr.run(_recorder_run)
    time.sleep(1)
    chunk = np.random.normal(size=(68,256))
    recdr.queue_put(('start', None))
    for i in range(160):
        chunk = np.random.normal(size=(68, 256))
        recdr.queue_put(('data', chunk))
        time.sleep(1 / 16)
    chunk = np.random.normal(size=(68,256))
    recdr.queue_put(('finish', None))
    time.sleep(10)
    print('stop')


