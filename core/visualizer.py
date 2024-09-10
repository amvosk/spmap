
import sys
import numpy as np
import scipy.signal as sg
sys.path.insert(0, '../utils/')

from filters import NotchFilterRealtime, ButterFilterRealtime, DownsamplerRealtime

# from recorder import Recorder


class Visualizer:
    def __init__(self, config, em):
        # initialize basic configuration
        self.config = config
        self.em = em

        self.fs_downsample = 1024
        self.filter_antialias = None
        self.filter_downsample = None
        self.notch_filter = None
        self.ecog_highpass = None
        self.ecog_lowpass = None
        self.hg_ecog_bandpass = None
        self.hg_ecog_smoother = None
        self.sound_highpass = None

        self.update_filters(self.config)
        self.em.register_handler('update config.processor.channels', self.update_filters)
        self.em.register_handler('update config.visualizer parameters', self.update_filters)
        self.em.register_handler('visualizer.chunk_visualize', self.chunk_visualize)

    def chunk_visualize(self, data):
        chunk_timeseries = data[:self.config.receiver.n_channels_max,...][self.config.processor.channels]
        if self.config.visualizer.ecog_notch:
            chunk_timeseries = self.notch_filter(chunk_timeseries)
        if self.config.visualizer.ecog_highpass_filter:
            chunk_timeseries = self.ecog_highpass(chunk_timeseries)
        if self.config.visualizer.ecog_lowpass_filter:
            chunk_timeseries = self.ecog_lowpass(chunk_timeseries)

        chunk_timeseries_hg = self.hg_ecog_bandpass(chunk_timeseries)
        chunk_timeseries_hga = np.abs(chunk_timeseries_hg)
        if self.config.visualizer.log_transform:
            chunk_timeseries_hga = np.log(chunk_timeseries_hga + 1e-10)
        chunk_timeseries_hga = self.hg_ecog_smoother(chunk_timeseries_hga)

        if self.config.visualizer.downsample:
            chunk_timeseries = self.filter_antialias(chunk_timeseries)
            chunk_timeseries = self.filter_downsample(chunk_timeseries)
            chunk_timeseries_hg = self.filter_downsample(chunk_timeseries_hg)
            chunk_timeseries_hga = self.filter_downsample(chunk_timeseries_hga)

        data_values = {
            'ECoG': chunk_timeseries,
            'hgECoG': chunk_timeseries_hg,
            'hgA': chunk_timeseries_hga,
        }
        self.em.trigger('gui.canvas_timeseries.update_data', data_values)

        chunk_sound = data[self.config.receiver.sound_channel_index]
        chunk_sound = self.sound_highpass(chunk_sound)
        if self.config.visualizer.downsample:
            chunk_sound = self.filter_downsample(chunk_sound)
        self.em.trigger('gui.canvas_sound.update_data', chunk_sound)

    def update_filters(self, args=None):
        self.filter_antialias = ButterFilterRealtime(
            freq=self.fs_downsample/4,
            fs=self.config.processor.fs,
            btype='low',
            order=4,
        )

        self.filter_downsample = DownsamplerRealtime(self.config.processor.fs, self.config.visualizer.fs_downsample)

        self.notch_filter = NotchFilterRealtime(
            notch_freqs=np.asarray([50, 100, 150, 200, 250]),
            Q=self.config.visualizer.notch_q,
            fs=self.config.processor.fs
        )

        self.ecog_highpass = ButterFilterRealtime(
            freq=self.config.visualizer.ecog_hpf,
            fs=self.config.processor.fs,
            btype='high',
            order=4,
        )

        self.ecog_lowpass = ButterFilterRealtime(
            freq=self.config.visualizer.ecog_lpf,
            fs=self.config.processor.fs,
            btype='low',
            order=4,
        )

        self.hg_ecog_bandpass = ButterFilterRealtime(
            freq=[self.config.visualizer.hg_ecog_bpfl, self.config.visualizer.hg_ecog_bpfh],
            fs=self.config.processor.fs,
            btype='bandpass',
            order=4,
        )

        self.hg_ecog_smoother = ButterFilterRealtime(
            freq=self.config.visualizer.hg_ecog_sf,
            fs=self.config.processor.fs,
            btype='low',
            order=4,
        )

        self.sound_highpass = ButterFilterRealtime(
            freq=10,
            fs=self.config.processor.fs,
            btype='high',
            order=4,
        )


if __name__ == '__main__':
    pass
