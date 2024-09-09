# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 01:14:12 2024

@author: Magomed
"""

import sys
import numpy as np
import scipy.signal as sg
import einops
sys.path.insert(0, '../utils/')

from filters import NotchFilter, ButterFilterRealtime, Downsampler


class Epoch:
    def __init__(self, epoch_chunks):
        print('epoch chunks count', np.array([epoch_chunks[i][0] for i in range(len(epoch_chunks))]).shape)
        #self.ieeg = einops.rearrange(epoch_chuks[:, 0, ... ], 'd c t -> c (d t)', t = 256)
        self.ieeg = np.concatenate([chunk[0] for chunk in epoch_chunks], axis=-1)  #d c t -> c (d t), t = 256
        print('self.ieeg', self.ieeg.shape)
        self.sound = np.concatenate([chunk[1] for chunk in epoch_chunks], axis=-1)
        self.label = np.concatenate([chunk[2] for chunk in epoch_chunks], axis=-1)

class EpochList:
    def __init__(self, bad_channels_mask, epoch_length, baseline_index, em):
        self.fs = 4096
        self.ds_coef = 4
        self.epoch_length = int(epoch_length / self.ds_coef)
        self.ecog_tensor = np.zeros((0, self.epoch_length, 20))  # Tensor (b t c)
        self.baseline = baseline_index
        self.ecog_power = None
        self.bad_channels_mask = bad_channels_mask
        self.em = em
        # self.em.trigger('update config.receiver.bad_channels', self.car) !!!!!!!!!

    def add(self, epoch):
        ecog = epoch.ieeg

        notch_filter = NotchFilter(notch_freqs=np.arange(50, 350, 50), Q=30, fs=self.fs)
        ecog_notch = notch_filter(ecog)
        ecog_bandpass = self._filter(ecog_notch, freq=[70, 130], fs=4096, order=4, btype='bandpass', axis=1)
        ecog_decimator = Downsampler(q=self.ds_coef, fs=4096)
        ecog_filtered = ecog_decimator(ecog_bandpass)

        print('ieeg_filtered.shape', ecog_filtered.shape)
        self.ecog_tensor = np.concatenate((self.ecog_tensor, ecog_filtered.reshape(1, *ecog_filtered.T.shape)),
                                          axis=0)  # (b t c) -> (b+1 t c)
        self.car()
        self.create_relative_power()

    def car(self):
        ecog_car = self.ecog_tensor - self.ecog_tensor[..., ~self.bad_channels_mask].mean(axis=-1, keepdims=True)
        print('bad chs  mean  b t 1', self.ecog_tensor[..., ~self.bad_channels_mask].mean(axis=-1, keepdims=True).shape)
        self.ecog_power = ecog_car ** 2

    def _filter(self, x, freq, fs, order, btype, axis=1):
        b, a = sg.butter(order, np.asarray(freq) / (fs / 2), btype=btype, output='ba')
        x = sg.filtfilt(b, a, x, axis=axis)
        return x

    def get_epochs(self):
        return self.epochs

    def create_relative_power(self):
        pre_indices = np.arange(0, self.baseline + 1, 1)
        epoch_indices = np.arange(self.baseline + 1, self.epoch_length)
        power = self.ecog_power
        logpower = 10 * np.log10(power + 1e-7)
        baseline = logpower[:, pre_indices, :]
        epochs = logpower[:, epoch_indices, :]
        print('baseline shape b t c', baseline.shape)

        baseline_mean = einops.reduce(baseline, 'b t c -> b 1 c', 'mean')
        print('baseline mean b 1 c', baseline_mean.shape)
        epochs_downsample = epochs  # einops.reduce(epochs, 'b (t q) c -> b t c', 'mean', q=4)

        epochs_relative_logpower = epochs_downsample - baseline_mean
        print(epochs_relative_logpower.shape)
        relative_logpower = einops.reduce(epochs_relative_logpower, 'b t c -> t c', 'mean')
        print('final magnitude', relative_logpower.shape)
        self.em.trigger('change results', relative_logpower.T)
        return relative_logpower

class Summary:
    def __init__(self, config, em):
        print('summary created')
        self.em = em
        self.config = config
        self.em.register_handler('summary.update', self.add_chunk)

        self.bad_channel_mask = np.zeros(20, dtype=bool)
        self.bad_channel_mask[[16, 17]] = True  # config.processor.channels_bad

        self.chunk_size = self.config.receiver.cache_size
        self.fs = 4096
        self.decimate_coef = 4
        self.baseline_period = (-0.8, -0.2)
        self.stimulus_period = (0, 3)

        self.info_buffer = []
        self.ieeg = None
        self.stimulus_indices = []
        self.pause_indices = []

        self.after_stimulus_flag = False
        self.after_stimulus_counter = 0

        self.chunk_counter = 0
        self.epoch_length = (int(self.fs / self.chunk_size * (self.stimulus_period[1] - self.baseline_period[
            0]))) * self.chunk_size  # Сломанное округление int, не получается сократить выражение на chunk size
        self.epochs = EpochList(self.bad_channel_mask, self.epoch_length,
                                int(self.baseline_period[1] - self.baseline_period[0] * self.fs), self.em)

    def add_chunk(self, chunk):
        print(chunk.shape)
        chunk_ieeg = chunk[:20]
        chunk_sound = chunk[self.config.receiver.sound_channel_index]
        chunk_flags = chunk[self.config.receiver.stimulus_channel_index]
        print('chunk flag', 1 in chunk_flags)
        # Обработка паузы - выкинуть из буфера все чанки этой эпохи (или просто очистить буфер??)
        pause_flag = np.where(chunk_flags == -1)[0]
        if len(pause_flag) > 0:
            pause_index = pause_flag[0]
            self.info_buffer.clear()
            self.pause_indices.append(pause_index + self.chunk_counter * self.chunk_size)
            self.after_stimulus_flag = False
            self.after_stimulus_counter = 0
            print("Pause event. Last Epoch has been removed")
            return

        self.info_buffer.append((chunk_ieeg, chunk_sound, chunk_flags))

        stimulus_flag = np.where(chunk_flags == 1)[0]
        if len(stimulus_flag) > 0:
            stimulus_index = stimulus_flag[0]
            print('stim index', stimulus_index)
            self.stimulus_indices.append(stimulus_index + self.chunk_counter * self.chunk_size)
            self.after_stimulus_flag = True
            self.after_stimulus_counter = 0  # -1
        print('self after stimulus counter', self.after_stimulus_counter)
        if self.after_stimulus_flag:
            self.after_stimulus_counter += 1
            if self.after_stimulus_counter >= int(self.stimulus_period[1] * self.fs / self.chunk_size):
                print('self after stimulus counter', self.after_stimulus_counter)
                stimulus_chunk_index = self.stimulus_indices[-1] // self.chunk_size
                print('stimulus chunk index', stimulus_chunk_index)
                epoch_chunks = self.info_buffer[stimulus_chunk_index + int(
                    self.baseline_period[0] * self.fs / self.chunk_size): stimulus_chunk_index + int(
                    self.stimulus_period[1] * self.fs / self.chunk_size + 1)]
                # print('чанков в секунду', np.array(epoch_chunks).shape[0] / self.epoch_length * self.fs)
                print('чанков в эпохе', len(epoch_chunks))
                self.var = epoch_chunks
                epoch = Epoch(epoch_chunks)
                self.epochs.add(epoch)
                self.epochs.car()
                self.after_stimulus_flag = False
        self.chunk_counter += 1




