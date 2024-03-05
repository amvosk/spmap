import sys, os, time
import numpy as np
import h5py

sys.path.insert(0, '../core/')
sys.path.insert(0, '../config/')
from config import read_config_file, parse_config
from recorder import Recorder


def test_add(recdr, config):
    np.random.seed(0)
    n_chunks = 100
    for _ in range(n_chunks):
        chunk = np.random.normal(size=(config.receiver.cache_size, config.recorder.dataset_width))
        recdr.add(chunk)
    assert np.concatenate(recdr.memory, axis=0).shape == \
           (config.receiver.cache_size * n_chunks, config.recorder.dataset_width)


def test_save(recdr, config):
    recdr.save(config.recorder)
    assert os.path.isfile(str(config.recorder.save_path) + '.h5')


def test_clear(recdr, config):
    recdr.clear()
    assert type(recdr.memory) is list
    assert len(recdr.memory) == 0
    test_add(recdr, config)


if __name__ == '__main__':
    config_file_path = '../config/config_default.ini'
    config_ini = read_config_file(config_file_path)
    config = parse_config(config_ini)

    recdr = Recorder()
    test_add(recdr, config)
    test_save(recdr, config)
    time.sleep(3)
    test_clear(recdr, config)

    with h5py.File(str(config.recorder.save_path) + '.h5', 'r') as file:
        raw_data = file['raw_data'][()]
        fs = file.attrs['fs']
        channel_bads = file.attrs['channel_bads']
        channel_names = file.attrs['channel_names'].split('|')
        print('raw_data.shape:', raw_data.shape)
        print('fs:', fs)
        print('channel_bads.shape:', channel_bads.shape)
        print('channel_names:', channel_names[:3] + channel_names[-5:])
