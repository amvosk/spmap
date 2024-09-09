
import sys
import numpy as np
import scipy.signal as sg
sys.path.insert(0, '../utils/')

from filters import NotchFilterRealtime, ButterFilterRealtime, DownsamplerRealtime

# from recorder import Recorder


class Processor:
    def __init__(self, config, em, interface):
        # initialize basic configuration
        self.config = config
        self.em = em
        # self.interface = interface
        # self.recorder = Recorder()
        # self.receiver_queue_input = interface.receiver.queue_input
        self.receiver_queue_output = interface.receiver.queue_output
        self.recorder_queue_input = interface.recorder.queue_input
        self.fs_downsample = 1024
        self.filter_downsample_antialiasing = None
        # self.filter_downsample_antialiasing_hg = None
        self.filter_downsample = None
        self.spectrum = None
        self.hg_spectrum = None
        self.notch_filter = None
        self.ecog_highpass = None
        self.ecog_lowpass = None
        self.hg_ecog_bandpass = None
        self.hg_ecog_smoother = None
        self.sound_highpass = None

        self.update_filters(self.config)
        self.em.register_handler('update config.processor.channels', self.update_filters)
        self.em.register_handler('update config.visualizer parameters', self.update_filters)


    def on_timer(self, update_data_timeseries, update_data_sound):

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

                self.em.trigger('processor.chunk_record', data)

                chunk_timeseries = data[:self.config.receiver.n_channels_max,...][self.config.processor.channels]
                chunk_sound = data[self.config.receiver.sound_channel_index]
                chunk_timeseries_notched = self.notch_filter(chunk_timeseries)

                if self.config.visualizer.ecog_notch:
                    chunk_timeseries_plot = np.copy(chunk_timeseries_notched)
                else:
                    chunk_timeseries_plot = np.copy(chunk_timeseries)
                if self.config.visualizer.ecog_highpass_filter:
                    chunk_timeseries_plot = self.ecog_highpass(chunk_timeseries_plot)
                if self.config.visualizer.ecog_lowpass_filter:
                    chunk_timeseries_plot = self.ecog_lowpass(chunk_timeseries_plot)

                spec = self.spectrum(chunk_timeseries.T).T

                chunk_timeseries_hg = self.hg_ecog_bandpass(chunk_timeseries_notched)
                chunk_timeseries_hg_plot = np.copy(chunk_timeseries_hg)
                chunk_timeseries_hg_ = np.abs(chunk_timeseries_hg)
                if self.config.visualizer.log_transform:
                    chunk_timeseries_hg_ = np.log(chunk_timeseries_hg_ + 1e-10)
                chunk_timeseries_hga = self.hg_ecog_smoother(chunk_timeseries_hg_)
                chunk_timeseries_hga_plot = np.copy(chunk_timeseries_hga)

                hg_spec = self.hg_spectrum(chunk_timeseries_hg.T).T

                if self.config.visualizer.downsample:
                    chunk_timeseries_plot = self.filter_downsample_antialiasing(chunk_timeseries_plot)
                    chunk_timeseries_plot = self.filter_downsample(chunk_timeseries_plot)
                    chunk_timeseries_hg_plot = self.filter_downsample(chunk_timeseries_hg_plot)
                    chunk_timeseries_hga_plot = self.filter_downsample(chunk_timeseries_hga)

                data_values = {
                    'ECoG':chunk_timeseries_plot,
                    'Spec':spec,
                    'hgECoG':chunk_timeseries_hg_plot,
                    'hgSpec':hg_spec,
                    'hgA':chunk_timeseries_hga_plot,
                }
                update_data_timeseries(data_values)
                # print("timeseries updated")

                chunk_sound = self.sound_highpass(chunk_sound)
                chunk_sound = self.filter_downsample(chunk_sound)
                update_data_sound(chunk_sound)

                # import psutil
                #
                # # Get the current process ID
                # parent_pid = psutil.Process().pid
                #
                # # Get information about all running processes
                # all_processes = psutil.process_iter()
                #
                # # Iterate over all processes and check if they are children of the parent process
                # children_processes = []
                # for process in all_processes:
                #     try:
                #         # Get the parent process ID of the current process
                #         parent_process_id = process.ppid()
                #         # Check if the parent process ID matches the parent process ID we are interested in
                #         if parent_process_id == parent_pid:
                #             children_processes.append(process)
                #     except psutil.NoSuchProcess:
                #         # Ignore processes that no longer exist
                #         pass
                #
                # # Print information about the children processes
                # print()
                # for child_process in children_processes:
                #     print("Child PID:", child_process.pid, "Name:", child_process.name())
                # print()















    def update_filters(self, args=None):
        self.filter_downsample_antialiasing = ButterFilterRealtime(
            freq=self.fs_downsample/4,
            fs=self.config.processor.fs,
            btype='low',
            order=4,
        )

        self.filter_downsample = DownsamplerRealtime(self.config.processor.fs, self.config.visualizer.fs_downsample)
        self.spectrum = FFT(
            self.config.visualizer.spec_window_size,
            self.config.visualizer.spec_ecog_low,
            self.config.visualizer.spec_ecog_high,
            self.config.visualizer.spec_decay,
            self.config.processor.n_channels,
            self.config.processor.fs
        )

        self.hg_spectrum = FFT(
            self.config.visualizer.spec_window_size,
            self.config.visualizer.spec_hg_ecog_low,
            self.config.visualizer.spec_hg_ecog_high,
            self.config.visualizer.spec_decay,
            self.config.processor.n_channels,
            self.config.processor.fs
        )

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








class FFT:
    def __init__(self, spec_window_size, spec_low, spec_high, spec_decay, n_channels, fs):
        self.fft_exp_mean = np.ones(((spec_high - spec_low)*spec_window_size, n_channels))
        self.fft_buffer = np.zeros((spec_window_size * fs, n_channels))
        self.spec_window_size = spec_window_size
        self.hann = sg.windows.hann(spec_window_size * fs).reshape((-1,1))
        self.spec_low = spec_low
        self.spec_high = spec_high
        self.spec_decay = spec_decay
        self.counter = 0
        self.cutoff = 1 / spec_decay
        self.separator = 0

    def __call__(self, chunk):
        if self.separator + chunk.shape[0] < self.fft_buffer.shape[0]:
            self.fft_buffer[self.separator:self.separator+chunk.shape[0]] = chunk
            self.separator += chunk.shape[0]
        elif self.separator + chunk.shape[0] == self.fft_buffer.shape[0]:

            overshoot = self.separator + chunk.shape[0] - self.fft_buffer.shape[0]
            assert overshoot == 0, 'overshoot should be == 0'

            fft_buffer_windowed = self.fft_buffer * self.hann
            fft = np.fft.rfft(fft_buffer_windowed, axis=0)
            fft_segment = np.abs(fft)[self.spec_low*self.spec_window_size:self.spec_high*self.spec_window_size]
            self.fft_buffer[:self.fft_buffer.shape[0]//2] = self.fft_buffer[self.fft_buffer.shape[0]//2:]
            self.separator = self.fft_buffer.shape[0] // 2

            if self.counter < self.cutoff:
                self.fft_exp_mean = (self.fft_exp_mean * self.counter + fft_segment) / (self.counter + 1)
            else:
                self.fft_exp_mean = self.spec_decay * self.fft_exp_mean + (1-self.spec_decay) * fft_segment
            self.counter += 1

        result = np.log(np.copy(self.fft_exp_mean) + 1e-7)
        return result



if __name__ == '__main__':
    pass
