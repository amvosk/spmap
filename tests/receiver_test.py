import sys
import time

import numpy as np

sys.path.insert(0, '../core/')
sys.path.insert(0, '../config/')
from config import read_config_file, parse_config
from receiver import Receiver


def test_connect(recvr, config_receiver):
    print('TEST: test_connect')
    recvr.connect(config_receiver)
    return recvr


def test_disconnect(recvr):
    print('TEST: test_disconnect')
    recvr.disconnect()
    return recvr


def test_queue_put(recvr):
    print('TEST: test_queue_put')
    time.sleep(.5)
    recvr.queue_put({'experiment_state': 1})
    time.sleep(.5)
    recvr.queue_put({'control_index': 1, 'stimulus_index': 1})
    time.sleep(.5)
    assert recvr.receiver_queue_input.empty()
    return recvr


def test_queue_get(recvr):
    print('TEST: test_queue_get')
    memory = []
    while recvr.queue_size() > 0:
        key, value = recvr.receiver_queue_output.get()
        if key == 'chunk':
            memory.append(value)
    assert recvr.receiver_queue_output.empty()
    if len(memory) > 0:
        memory = np.concatenate(memory, axis=0)
        print(memory.shape)
    return recvr


if __name__ == '__main__':
    config_file_path = '../config/config_default.ini'
    config_ini = read_config_file(config_file_path)
    config = parse_config(config_ini)

    recvr = Receiver()

    recvr = test_connect(recvr, config.receiver)
    recvr = test_queue_put(recvr)
    recvr = test_disconnect(recvr)
    recvr = test_queue_get(recvr)
    recvr.clear()
    time.sleep(1)
