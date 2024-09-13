
import sys
import numpy as np
import scipy.signal as sg
sys.path.insert(0, '../utils/')

# from filters import NotchFilterRealtime, ButterFilterRealtime, DownsamplerRealtime

# from recorder import Recorder


class Processor:
    def __init__(self, config, em, interface):
        # initialize basic configuration
        self.config = config
        self.em = em

        self.receiver_queue_output = interface.receiver.queue_output
        self.recorder_queue_input = interface.recorder.queue_input
        self.fs_downsample = 1024
        self.filter_downsample_antialiasing = None
        self.filter_downsample = None
        self.spectrum = None
        self.hg_spectrum = None
        self.notch_filter = None
        self.ecog_highpass = None
        self.ecog_lowpass = None
        self.hg_ecog_bandpass = None
        self.hg_ecog_smoother = None
        self.sound_highpass = None

    def on_timer(self):
        if self.receiver_queue_output is None:
            print('receiver queue None')
            return
        if not self.receiver_queue_output.empty():
            message = self.receiver_queue_output.get(block=False)
            # print("receiver message{}".format(message))
            if message is None:
                return
            label, data = message
            if label == 'lost connection, data saved':
                return
            elif label == 'chunk':
                data = data.T

                self.em.trigger('recorder.chunk_record', data)
                self.em.trigger('visualizer.chunk_visualize', data)


if __name__ == '__main__':
    pass
