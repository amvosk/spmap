
import numpy as np
import scipy.signal as sg


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


class Downsampler:
    def __init__(self, fs, fs_downsample):
        self.downsample_coef = int(fs / fs_downsample)

    def __call__(self, chunk):
        chunk_downsampled = chunk[...,self.downsample_coef-1::self.downsample_coef]
        return chunk_downsampled


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