
import numpy as np
import scipy.signal as sg
import librosa


class ButterFilterRealtime:
    def __init__(self, freq, fs, btype, order=4):
        self.sos = sg.butter(order, np.asarray(freq), btype=btype, output='sos', fs=fs)
        self.zi = sg.sosfilt_zi(self.sos)

    def __call__(self, chunk):
        if chunk.ndim + 1 == self.zi.ndim and chunk.ndim == 2:
            assert chunk.shape[-2] == self.zi.shape[-2], f'chunk and zi mast have same number of channels, but {chunk.shape[-2]} and {self.zi.shape[-2]} provided'
        elif chunk.ndim != 1 and self.zi.ndim == 2:
            self.zi = np.repeat(np.expand_dims(self.zi, axis=-2), repeats=chunk.shape[-2], axis=-2)
        chunk_filtered, self.zi = sg.sosfilt(self.sos, chunk, zi=self.zi)
        return chunk_filtered


class ButterFilter:
    def __init__(self, freq, fs, btype, order=4):
        self.sos = sg.butter(order, np.asarray(freq), btype=btype, output='sos', fs=fs)

    def __call__(self, epoch):
        epoch_filtered = sg.sosfiltfilt(self.sos, epoch)
        return epoch_filtered




class DownsamplerRealtime:
    def __init__(self, fs, fs_downsample):
        self.downsample_coef = int(fs / fs_downsample)

    def __call__(self, chunk):
        chunk_downsampled = chunk[...,self.downsample_coef-1::self.downsample_coef]
        return chunk_downsampled


class Downsampler:
    def __init__(self, fs, fs_downsample, res_type='soxr_hq'):
        self.fs = fs
        self.fs_downsample = fs_downsample
        self.res_type = res_type

    def __call__(self, epoch):
        epoch_downsampled = librosa.resample(epoch, orig_sr=self.fs, target_sr=self.fs_downsample, res_type=self.res_type)
        return epoch_downsampled




class NotchFilterRealtime:
    def __init__(self, notch_freqs, Q, fs):
        sos, zi = [], []
        for freq in notch_freqs:
            b, a = sg.iirnotch(freq, freq / Q, fs)
            sos.append(np.concatenate([b, a]))
            zi.append(np.zeros(2))
        self.sos = np.stack(sos)
        self.zi = np.stack(zi)

    def __call__(self, chunk):
        if chunk.ndim + 1 == self.zi.ndim and chunk.ndim == 2:
            assert chunk.shape[-2] == self.zi.shape[-2], f'chunk and zi mast have same number of channels, but {chunk.shape[-2]} and {self.zi.shape[-2]} provided'
        elif chunk.ndim != 1 and self.zi.ndim == 2:
            self.zi = np.repeat(np.expand_dims(self.zi, axis=-2), repeats=chunk.shape[-2], axis=-2)
        chunk_filtered, self.zi = sg.sosfilt(self.sos, chunk, zi=self.zi)
        return chunk_filtered


class NotchFilter:
    def __init__(self, notch_freqs, Q, fs):
        sos = []
        for freq in notch_freqs:
            b, a = sg.iirnotch(freq, freq / Q, fs)
            sos.append(np.concatenate([b, a]))
        self.sos = np.stack(sos)

    def __call__(self, epoch):
        epoch_filtered = sg.sosfiltfilt(self.sos, epoch)
        return epoch_filtered


# class FFT:
#     def __init__(self, spec_window_size, spec_low, spec_high, spec_decay, n_channels, fs):
#         self.fft_exp_mean = np.ones(((spec_high - spec_low)*spec_window_size, n_channels))
#         self.fft_buffer = np.zeros((spec_window_size * fs, n_channels))
#         self.spec_window_size = spec_window_size
#         self.hann = sg.windows.hann(spec_window_size * fs).reshape((-1,1))
#         self.spec_low = spec_low
#         self.spec_high = spec_high
#         self.spec_decay = spec_decay
#         self.counter = 0
#         self.cutoff = 1 / spec_decay
#         self.separator = 0
#
#     def __call__(self, chunk):
#         if self.separator + chunk.shape[0] < self.fft_buffer.shape[0]:
#             self.fft_buffer[self.separator:self.separator+chunk.shape[0]] = chunk
#             self.separator += chunk.shape[0]
#         elif self.separator + chunk.shape[0] == self.fft_buffer.shape[0]:
#
#             overshoot = self.separator + chunk.shape[0] - self.fft_buffer.shape[0]
#             assert overshoot == 0, 'overshoot should be == 0'
#
#             fft_buffer_windowed = self.fft_buffer * self.hann
#             fft = np.fft.rfft(fft_buffer_windowed, axis=0)
#             fft_segment = np.abs(fft)[self.spec_low*self.spec_window_size:self.spec_high*self.spec_window_size]
#             self.fft_buffer[:self.fft_buffer.shape[0]//2] = self.fft_buffer[self.fft_buffer.shape[0]//2:]
#             self.separator = self.fft_buffer.shape[0] // 2
#
#             if self.counter < self.cutoff:
#                 self.fft_exp_mean = (self.fft_exp_mean * self.counter + fft_segment) / (self.counter + 1)
#             else:
#                 self.fft_exp_mean = self.spec_decay * self.fft_exp_mean + (1-self.spec_decay) * fft_segment
#             self.counter += 1
#
#         result = np.log(np.copy(self.fft_exp_mean) + 1e-7)
#         return result