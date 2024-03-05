import os
from os import makedirs
import time
from pathlib import Path
from threading import Thread

import time, copy
import multiprocessing
from dataclasses import dataclass

from pylsl import StreamInlet, resolve_byprop
import numpy as np

import scipy.io.wavfile
import numpy as np
import numpy.ma as ma
from matplotlib import pyplot as plt
import h5py
from scipy import signal
from sklearn.metrics import mutual_info_score
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import scipy.signal as sg

from statistics import preprocess_ecog, preprocess_sound, correlation, mutual_information, get_index
from statistics import EcogEnvelopeFilter, SoundEnvelopeFilter, NoiseEstimationFilter
from statistics import ttest, kstest, feature_phase

# from statsmodels.stats.multitest import multipletests


# from resultplot import ResultPlot



class Decoder:
    def __init__(self):
        # initialize basic configuration
        self.decoder_process = None
        self.decoder_queue_input = multiprocessing.Queue()
        self.decoder_queue_output = multiprocessing.Queue()

    def queue_put(self, input_):
        self.decoder_queue_input.put(input_)

    def queue_get(self):
        return self.decoder_queue_output.get()

    def queue_empty(self):
        return self.decoder_queue_output.empty()

    def queue_size(self):
        return self.decoder_queue_output.qsize()

    # def connect(self, config_receiver):
    #     try:
    #         self.receiver_process = multiprocessing.Process(
    #             target=_connect,
    #             args=(config_receiver, self.receiver_queue_input, self.decoder_queue_output)
    #         )
    #         # self.recorder_process.daemon = True
    #         self.receiver_process.start()
    #     except ConnectionError:
    #         print('connection error')
    #         if self.receiver_process.is_alive():
    #             self.receiver_process.join()
    #         if self.receiver_process.is_alive():
    #             self.receiver_process.terminate()

    def disconnect(self):
        try:
            self.queue_put({'connection_state': 0})
        except AttributeError as exc:
            print('No process available to disconnect')

    def clear(self):
        if self.decoder_process.is_alive():
            self.decoder_process.join()
        if self.decoder_process.is_alive():
            self.decoder_process.terminate()
        self.decoder_process = None
        self.decoder_queue_input = multiprocessing.Queue()
        self.decoder_queue_output = multiprocessing.Queue()





















class Decoder:
    def __init__(self, config, qs):

        # self.recorder = recorder
        self.config = config

        self.GRID_X = self.config['decoder'].getint('grid_size_x')
        self.GRID_Y = self.config['decoder'].getint('grid_size_y')

        self.nchannels = self.GRID_X * self.GRID_Y
        self.GRID_CHANNEL_FROM = self.config['decoder'].getint('grid_channel_from')
        self.ch_idxs_ecog = np.arange(self.GRID_CHANNEL_FROM, self.GRID_CHANNEL_FROM + self.nchannels) - 1

        self.q_from_recorder_to_decoder = qs['q_from_recorder_to_decoder']
        self.q_from_decoder_to_ui = qs['q_from_decoder_to_ui']

        if config['general'].getboolean('objects_mode') or config['general'].getboolean('actions_mode'):
            self.single_stimulus_time = self.config['display pictures'].getfloat('single_picture_time')
        elif config['general'].getboolean('questions_mode'):
            self.single_stimulus_time = 3
        self.phase_lag_backward = self.config['decoder'].getfloat('phase_lag_backward')
        self.baseline_backward_time = self.config['decoder'].getfloat('baseline_backward_time')

        self.thr_50hz = config['decoder'].getfloat('thr_50hz')
        self.fs = config['recorder'].getint('fs')
        self.fband = [config['decoder'].getint('fmin'), config['decoder'].getint('fmax')]
        self.flow = 40
        self.running_mean_coef = 0.5
        self.eps = 1e-7

        self.NoiseEstimationFilter_50hz = NoiseEstimationFilter(self.nchannels, [48, 52], self.fs)
        self.NoiseEstimationFilter_HIGH = NoiseEstimationFilter(self.nchannels, [400, 600], self.fs)
        self.EcogEnvelopeFilter = EcogEnvelopeFilter(self.nchannels, self.fband, self.flow, self.fs, order=4)
        self.SoundEnvelopeFilter = SoundEnvelopeFilter(0.5, self.flow, self.fs, order=4, eps=1e-7)

        self.noise_estimator_50hz = np.zeros(self.nchannels)
        self.noise_estimator_HIGH = np.zeros(self.nchannels)

        self.ecog_env_cont = np.zeros((0, self.nchannels))
        self.sound_env_cont = np.zeros(0)
        self.pindex = np.zeros(0)
        self.current_epoch_type = -1

        self.logpower_stimulus = []
        self.logpower_change_stimulus = []
        self.mutinfo_stimulus = []
        self.phase_stimulus = []

        self.logpower_control = []
        self.logpower_change_control = []
        self.mutinfo_control = []

        self.thread = Thread(target=self.realtime, args=())

    def start(self):
        self.thread.start()

    def preprocess_chunk(self, chunk):
        chunk_ecog = chunk[:, self.ch_idxs_ecog]
        chunk_sound = chunk[:, 64]
        chunk_pindex = chunk[:, 70]

        bad_channels = self.noise_estinamtion(chunk_ecog)
        chunk_ecog_env = self.EcogEnvelopeFilter(chunk_ecog)
        chunk_sound_env = self.SoundEnvelopeFilter(chunk_sound)
        return chunk_ecog_env, chunk_sound_env, chunk_pindex, bad_channels

    def noise_estinamtion(self, chunk_ecog):
        chunk_noise_50hz = self.NoiseEstimationFilter_50hz(chunk_ecog)
        chunk_noise_50hz_update = np.log(np.mean(chunk_noise_50hz ** 2 + self.eps, axis=0))
        self.noise_estimator_50hz = self.noise_estimator_50hz * self.running_mean_coef + (
                    1 - self.running_mean_coef) * chunk_noise_50hz_update
        # print(self.noise_estimator_50hz)
        bad_channels_50hz = self.noise_estimator_50hz > self.thr_50hz

        # chunk_noise_HIGH = self.NoiseEstimationFilter_HIGH(chunk_ecog)
        # chunk_noise_HIGH_update = np.mean(np.log(np.abs(chunk_noise_HIGH) + eps), axis=0)
        # self.noise_estimator_HIGH = self.noise_estimator_HIGH*self.running_mean_coef + (1-self.running_mean_coef)*chunk_noise_HIGH_update
        # noise_estimator_HIGH_median = np.median(self.noise_estimator_HIGH)
        # noise_estimator_HIGH_std = np.std(self.noise_estimator_HIGH)
        # bad_channels_HIGH = np.logical_or(self.noise_estimator_HIGH > noise_estimator_HIGH_median + 3*noise_estimator_HIGH_std,
        #                                  self.noise_estimator_HIGH < noise_estimator_HIGH_median - 3*noise_estimator_HIGH_std)
        # bad_channels = np.logical_or(bad_channels_50hz, bad_channels_HIGH)
        return bad_channels_50hz

    def realtime(self):

        while True:
            if self.q_from_recorder_to_decoder.empty():
                time.sleep(0.001)
            else:
                chunk = self.q_from_recorder_to_decoder.get()
                if type(chunk) is str:
                    break
                chunk_ecog_env, chunk_sound_env, chunk_pindex, bad_channels = self.preprocess_chunk(chunk)
                # print(bad_channels)

                self.ecog_env_cont = np.concatenate([self.ecog_env_cont, chunk_ecog_env], axis=0)
                self.sound_env_cont = np.concatenate([self.sound_env_cont, chunk_sound_env], axis=0)
                self.pindex = np.concatenate([self.pindex, chunk_pindex], axis=0)

                stop = np.where(self.pindex < 0)[0]
                # print(self.ecog_env_cont.shape)

                if len(stop) > 0:
                    stop = stop[0]
                    start = np.where(self.pindex > 0)[0]
                    start = start[0]

                    # is epoch if type stimulus (0) or control (1)
                    epoch_type = self.pindex[start] < 50

                    epoch_trans = self.ecog_env_cont[start - int(self.fs * self.phase_lag_backward):start + int(
                        self.fs * self.single_stimulus_time)]
                    epoch_effect = self.ecog_env_cont[start:stop + 1]
                    epoch_baseline = self.ecog_env_cont[start - int(self.fs * self.baseline_backward_time):start:start]

                    self.ecog_env_cont = self.ecog_env_cont[stop + 1:]

                    self.pindex = self.pindex[stop + 1:]

                    logpower = np.log(np.mean(epoch_effect ** 2, axis=0) + self.eps)
                    logpower_change = logpower - np.log(np.mean(epoch_baseline ** 2, axis=0) + self.eps)

                    ramp = np.linspace(0, 1, epoch_trans.shape[0])

                    mutinfo = self.mutual_information(epoch_trans, ramp)
                    phase = feature_phase(epoch_trans)

                    if epoch_type:
                        self.logpower_stimulus.append(logpower)
                        self.logpower_change_stimulus.append(logpower_change)
                        self.mutinfo_stimulus.append(mutinfo)
                        self.phase_stimulus.append(phase)
                    else:
                        self.logpower_control.append(logpower)
                        self.logpower_change_control.append(logpower_change)
                        self.mutinfo_control.append(mutinfo)
                        # self.phase_control.append(phase)

                    # statistics
                    neglog_pvalue_logpower, neglog_pvalue_logpower_change, neglog_pvalue_mutinfo, neglog_pvalue_phase = [
                        np.zeros(self.nchannels) for _ in range(4)]

                    if len(self.phase_stimulus) > 2:
                        phase_stimulus = np.stack(self.phase_stimulus)
                        neglog_pvalue_phase = - np.log10(kstest(phase_stimulus))

                    if len(self.logpower_stimulus) > 2 and len(self.logpower_control) > 2:
                        logpower_stimulus = np.stack(self.logpower_stimulus)
                        logpower_control = np.stack(self.logpower_control)
                        neglog_pvalue_logpower = -np.log10(ttest(logpower_stimulus, logpower_control))

                        logpower_change_stimulus = np.stack(self.logpower_change_stimulus)
                        logpower_change_control = np.stack(self.logpower_change_control)
                        neglog_pvalue_logpower_change = -np.log10(
                            ttest(logpower_change_stimulus, logpower_change_control))

                        mutinfo_stimulus = np.stack(self.mutinfo_stimulus)
                        mutinfo_control = np.stack(self.mutinfo_control)
                        neglog_pvalue_mutinfo = -np.log10(ttest(mutinfo_stimulus, mutinfo_control))

                    # print(np.copy(bad_channels).astype(float))
                    plot_dict = {
                        'noise50hz': np.copy(self.noise_estimator_50hz),
                        'bad_channels': np.copy(bad_channels).astype(int),
                        'neglog_pvalue_logpower': np.copy(neglog_pvalue_logpower),
                        'neglog_pvalue_logpower_change': np.copy(neglog_pvalue_logpower_change),
                        'neglog_pvalue_mutinfo': np.copy(neglog_pvalue_mutinfo),
                        'neglog_pvalue_phase': np.copy(neglog_pvalue_phase)
                    }
                    self.q_from_decoder_to_ui.put(plot_dict)

    def make_ramp1(self, length, length_total, higth):
        ramp = np.zeros(length_total)
        ramp[:length] = np.linspace(0, higth, length)
        return ramp

    def make_ramp2(self, length, length_total, higth):
        ramp = np.zeros(length_total)
        ramp[-length:] = np.linspace(0, higth, length)
        return ramp

    def _mutual_information(self, x, y, bins):
        c_xy, b1, b2 = np.histogram2d(x, y, bins)
        mi = mutual_info_score(None, None, contingency=c_xy)
        return mi

    def mutual_information(self, ecog_env, sound_env, clip_alpha=0.99, bins=32):

        q = np.quantile(ecog_env, clip_alpha, axis=0)
        sound_entropy = self._mutual_information(sound_env, sound_env, bins)
        mi = []
        for i in range(ecog_env.shape[1]):
            ecog_env_in_channel = ecog_env[:, i]
            # clip
            ecog_env_in_channel[ecog_env_in_channel > q[i]] = q[i]

            ecog_entropy = self._mutual_information(ecog_env_in_channel, ecog_env_in_channel, bins)
            ecog_entropy = ecog_entropy if ecog_entropy > self.eps else 1000

            mi_channel = self._mutual_information(ecog_env_in_channel, sound_env, bins) / np.sqrt(
                sound_entropy * ecog_entropy)
            mi.append(mi_channel)
        return np.asarray(mi)

    def process_current_file(self):
        scores = self.process_file(self.experiment_data_path)
        self.plot_results(scores)

    def process_file(self, path):
        print(path)
        scores = []
        for group in ['data_objects', 'data_actions']:
            self._printm('Processing ' + group);
            with h5py.File(path, 'r+') as file:
                raw_data = np.array(file[group]['raw_data'])
                # picture_indices = np.array(file[group]['picture_indices'])
                fs = int(file['fs'][()])
            if raw_data.shape[0] > 4096 * 10:
                scores.append(self.process_data(group, raw_data, fs))
        return scores

    # process raw data,
    def process_data(self, name, raw_data, fs):
        # range of channels with eeg data, e.g. for grid 1 to 20 => range(0, 20) ~ [0, 1, ..., 19]
        ch_idxs_ecog = np.arange(self.GRID_CHANNEL_FROM, self.GRID_CHANNEL_FROM + self.nchannels) - 1

        score = Score()
        score.name = name

        # copy ecog and stim data
        ecog = np.copy(raw_data[:, ch_idxs_ecog])
        sound = raw_data[:, 64]
        pindex = raw_data[:, 72]

        dsfs = 100
        time_length = 3

        pictures_index, baseline_index = get_index(pindex)

        sound_envs_pictures, sound_envs_baseline = preprocess_sound(sound, dsfs, fs, pictures_index, baseline_index,
                                                                    time_length)
        noise_estimate, ecog_envs_pictures, ecog_envs_baseline = preprocess_ecog(ecog, dsfs, fs, pictures_index,
                                                                                 baseline_index, time_length)

        score.noise50hz = np.log(noise_estimate + 1)
        score.bad_channels = np.log(noise_estimate + 1) > self.TH50HZ

        if self.n_pictures_baseline > 0:
            score.corr = correlation(ecog_envs_pictures, ecog_envs_baseline)
        else:
            score.corr = np.zeros(ecog_envs_pictures.shape[-1])
        score.mi = mutual_information(ecog_envs_pictures, sound_envs_pictures, clip_alpha=0.99, bins=10)

        return score

    def plot_results(self, scores):
        plt.close('all')
        plot_shape = (len(scores), 3)
        fig, ax = plt.subplots(nrows=plot_shape[0],
                               ncols=plot_shape[1],
                               figsize=(12, int(3.5 * plot_shape[0]) + 1))

        col_titles = ['correlation', 'mutual information', '50Hz']

        viridis_cm = plt.cm.get_cmap('viridis', 256)
        viridis_cm.set_bad('black', 1)

        def array_into_grid(array):
            return (array.reshape([self.GRID_X, self.GRID_Y]).T)[::-1, :]

        ecog_channel_grid = array_into_grid(np.arange(self.GRID_CHANNEL_FROM, self.GRID_CHANNEL_FROM + self.nchannels))
        print(ecog_channel_grid)
        for i, score in enumerate(scores):
            values = score.corr, score.mi, score.noise50hz
            print(score.corr, score.mi)
            bad_channels = score.bad_channels
            row_title = score.name[5:]
            for j, value in enumerate(values):
                plt.subplot(plot_shape[0], plot_shape[1], (i * plot_shape[1] + j + 1))

                im = array_into_grid(value)
                # bad_channels = np.logical_or(scores[i].data_i.bad_ch, scores[i].data_j.bad_ch)
                if j != 2:
                    im = ma.masked_array(im, array_into_grid(bad_channels))

                plt.imshow(im, cmap=viridis_cm)  # , vmin=min_score, vmax=max_score)
                plt.colorbar()

                for m in range(self.GRID_Y):
                    for n in range(self.GRID_X):
                        plt.text(n, m, str(ecog_channel_grid[m, n]), color='white', ha='center', va='center')
                plt.plot([0.5, 0.5], [-0.5, 1.5], color='silver', lw=2)
                plt.plot([2.5, 2.5], [-0.5, 1.5], color='silver', lw=2)
                plt.title(col_titles[j]);
                if j == 0:
                    plt.text(-10, 5, row_title, size=24)
                plt.axis("off")


    def _printm(self, message):
        print('{} {}: '.format(time.strftime('%H:%M:%S'), type(self).__name__) + message)


class Score:
    def __init__(self):
        self.name = None
        self.noise50hz = None
        self.bad_channels = None
        self.corr = None
        self.mi = None


# if __name__ == '__main__':
#     import configparser
#
#     config = configparser.ConfigParser()
#     config.read(Path('decoder.py').resolve().parents[1] / 'util/custom_config_processing.ini')