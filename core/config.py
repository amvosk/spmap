# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 09:37:29 2020

@author: dblok
"""

import math
import configparser
import copy
from pathlib import Path
from os import makedirs
import time
from dataclasses import dataclass, fields
import json

import numpy as np

class LocalConfig:
    split = 0
    splits_values = [np.asarray([])]

    def __init__(self, config, em):
        self.config = config
        self.em = em
        self.em.register_handler('update local.split', self._update_local_split)
        self.em.register_handler('update local.splits_values', self._update_local_splits_values)

    def _update_local_split(self, split):
        self.split = int(split)

    def _update_local_splits_values(self, stimulus):
        self.splits_values = stimulus.get_splits()


@dataclass
class GeneralConfig:
    debug_mode: bool

    def __post_init__(self):
        self._type = 'general'


@dataclass
class PatientInfoConfig:
    patient_name: str
    patient_date: str

    def __post_init__(self):
        self._type = 'patient_info'


@dataclass
class PathConfig:
    data_path: Path
    app_path: Path
    resource_path: Path

    def __post_init__(self):
        self._type = 'path'


@dataclass
class ExperimentConfig:
    stimulus_type: str
    n_stimulus: int
    # stimulus_time -> show stimulus for %stimulus_time% seconds
    stimulus_time: float
    switch_time: float

    def __post_init__(self):
        self._type = 'experiment'


@dataclass
class ReceiverConfig:
    amplifier: str
    amplifier_ip: str
    lsl_stream_name: str
    lsl_stream_name_debug: str
    fs: int
    cache_size: int
    cache_width: int
    n_channels_max: int
    sound_channel_index: int
    timestamp_channel_index: int
    control_channel_index: int
    stimulus_channel_index: int
    control_indices: dict

    def __post_init__(self):
        self._type = 'receiver'

    def _update_amplifier(self, amplifier):
        self.amplifier = amplifier
        if amplifier == 'EBNeuro_BePLusLTM':
            self.lsl_stream_name = amplifier + '_' + self.amplifier_ip
        else:
            self.lsl_stream_name = amplifier

    def _update_amplifier_ip(self, amplifier_ip):
        self.amplifier_ip = amplifier_ip
        self.lsl_stream_name = self.amplifier + '_' + amplifier_ip

    # def _update_channels(self, channels):
    #     self.channels = np.copy(channels)
    #     self.n_channels = np.sum(self.channels).item()


# @dataclass
# class RecorderConfig:
#     # save_path: Path
#     fs: int
#     channel_index: np.ndarray
#     channels_bad: np.ndarray
#     channel_names: list
#     dataset_width: int
#
#     def __post_init__(self):
#         self._type = 'recorder'
#
#     def _update_channels_bad(self, data):
#         index, state = data
#         self.channels_bad[index] = not state
#         # em.trigger('update config.recorder.channels_bad', self)


@dataclass
class DecoderConfig:
    envelope_fmin: int
    envelope_fmax: int
    envelope_fstep: int

    def __post_init__(self):
        self._type = 'decoder'


@dataclass
class ProcessorConfig:
    channels: np.ndarray
    n_channels: int
    n_channels_grid: int
    n_rows: int
    n_columns: int
    grid_type: str
    fs: int
    channel_index: np.ndarray
    channels_bad: np.ndarray
    channel_names: list
    dataset_width: int

    def __post_init__(self):
        self._type = 'processor'

    def _update_grid_type(self, grid_type):
        self.grid_type = grid_type
        n_channels_grid, n_rows, n_columns = list(map(int, grid_type.split(',')))
        self.n_channels_grid = n_channels_grid
        self.n_rows = n_rows
        self.n_columns = n_columns

    def _update_channels(self, channels):
        self.channels = np.copy(channels)
        self.n_channels = np.sum(self.channels).item()
        self.channels_bad = np.zeros(self.n_channels, dtype=bool)
        # print()
        # print(self.channels)
        # print(self.n_channels)
        # print(self.channels_bad)

    def _update_channels_bad(self, data):
        index, state = data
        self.channels_bad[index] = not state


@dataclass
class VisualizerConfig:
    # size of the window
    downsample: bool
    fs_downsample: int
    n_samples_timeseries_sec: float
    n_samples_timeseries: int
    n_samples_timeseries_sound_sec: float
    n_samples_timeseries_sound: int
    vis_view: str
    notch_q: float
    notch_n: int
    ecog_hpf: float
    ecog_lpf: float
    hg_ecog_bpfl: float
    hg_ecog_bpfh: float
    log_transform: bool
    hg_ecog_sf: float
    spec_ecog_low: int
    spec_ecog_high: int
    spec_hg_ecog_low: int
    spec_hg_ecog_high: int
    spec_window_size: int
    spec_decay: float
    ecog_notch: bool
    ecog_highpass_filter: bool
    ecog_lowpass_filter: bool

    def __post_init__(self):
        self._type = 'visualizer'

    def _update_n_samples_plot_sec(self, config, n_samples_plot_sec):
        self.n_samples_plot_sec = float(n_samples_plot_sec)
        if self.downsample:
            self.n_samples_plot = int(self.fs_downsample * self.n_samples_plot_sec)
        else:
            self.n_samples_plot = int(config.receiver.fs * self.n_samples_plot_sec)



@dataclass
class Config:
    patient_info: PatientInfoConfig
    general: GeneralConfig
    paths: PathConfig
    experiment: ExperimentConfig
    processor: ProcessorConfig
    receiver: ReceiverConfig
    # recorder: RecorderConfig
    decoder: DecoderConfig
    visualizer: VisualizerConfig

    def save(self, path):
        write_config_file(path, self)

    def handle_event_config_save(self):
        self.save(self.paths.app_path / 'config/config.ini')

data_classes = [
    PatientInfoConfig, GeneralConfig, PathConfig,
    ExperimentConfig, ReceiverConfig, ProcessorConfig,
    # RecorderConfig,
    DecoderConfig, VisualizerConfig
]

for i, DataClass in enumerate(data_classes):
    for field in fields(DataClass):
        method_name = "_update_{}".format(field.name)
        method = getattr(DataClass, method_name, None)
        if not method:
            if field.type == str:
                def method(self, new_value, field=field):
                    setattr(self, field.name, str(new_value))
            elif field.type == int:
                def method(self, new_value, field=field):
                    setattr(self, field.name, int(new_value))
            elif field.type == float:
                def method(self, new_value, field=field):
                    setattr(self, field.name, float(new_value))
            elif field.type == bool:
                def method(self, new_value, field=field):
                    setattr(self, field.name, bool(new_value))
            if method:
                setattr(DataClass, '_update_{}'.format(field.name), method)


    def method_(self, em):
        for field_name, _ in copy.deepcopy(vars(self)).items():
            method_name_ = "_update_{}".format(field_name)
            method_ = getattr(self, method_name_, None)
            if method_:
                em.register_handler('update config.{}.{}'.format(self._type, field_name), method_)
                # print('update config.{}.{}'.format(self._type, field_name))
    setattr(DataClass, 'set_events_handlers', method_)



def read_config_file(path='config.ini'):
    config = configparser.ConfigParser()
    config.read(path)
    return config


def parse_config(em, config):
    patient_name = config['patient_info']['patient_name']
    patient_date = config['patient_info']['patient_date']
    patient_info_config = PatientInfoConfig(
        patient_name=patient_name,
        patient_date=patient_date)
    patient_info_config.set_events_handlers(em)

    # control_type = config['general'].getint('control_type')
    debug_mode = config['general'].getboolean('debug_mod')
    general_config = GeneralConfig(
        debug_mode=debug_mode
    )
    general_config.set_events_handlers(em)

    data_path = Path(config['path']['data_path'])
    app_path = Path(__file__).resolve().parents[1]
    resource_path = app_path / 'resource'

    path_config = PathConfig(
        data_path=data_path,
        app_path=app_path,
        resource_path=resource_path
    )
    path_config.set_events_handlers(em)

    stimulus_type = config['experiment']['stimulus_type']
    n_stimulus = config['experiment'].getfloat('n_stimulus')
    stimulus_time = config['experiment'].getfloat('stimulus_time')
    switch_time = config['experiment'].getfloat('switch_time')
    experiment_config = ExperimentConfig(
        stimulus_type=stimulus_type,
        n_stimulus=n_stimulus,
        stimulus_time=stimulus_time,
        switch_time=switch_time,
    )
    experiment_config.set_events_handlers(em)

    amplifier = config['receiver']['amplifier']
    amplifier_ip = config['receiver']['amplifier_ip']
    lsl_stream_name = amplifier + '_' + amplifier_ip
    lsl_stream_name_debug = config['receiver']['lsl_stream_name_debug']
    fs = config['receiver'].getint('fs')
    n_channels_max = config['receiver'].getint('n_channels_max')
    cache_size = config['receiver'].getint('cache_size')
    cache_width = config['receiver'].getint('cache_width')
    sound_channel_index = config['receiver'].getint('sound_channel_index')
    timestamp_channel_index = config['receiver'].getint('timestamp_channel_index')
    control_channel_index = config['receiver'].getint('control_channel_index')
    stimulus_channel_index = config['receiver'].getint('stimulus_channel_index')

    with open(app_path / 'config/stimulus/control_indices.json', 'r') as file:
        control_indices = json.load(file)

    receiver_config = ReceiverConfig(
        amplifier=amplifier,
        amplifier_ip=amplifier_ip,
        lsl_stream_name=lsl_stream_name,
        lsl_stream_name_debug=lsl_stream_name_debug,
        fs=fs,
        cache_size=cache_size,
        cache_width=cache_width,
        n_channels_max=n_channels_max,
        sound_channel_index=sound_channel_index,
        timestamp_channel_index=timestamp_channel_index,
        control_channel_index=control_channel_index,
        stimulus_channel_index=stimulus_channel_index,
        control_indices=control_indices,
    )
    receiver_config.set_events_handlers(em)

    grid_type = config['processor']['grid_type']
    n_channels_grid, n_rows, n_columns = list(map(int, grid_type.split(',')))
    n_channels = n_channels_grid
    if n_channels_grid > n_channels_max:
        n_channels = n_channels_max
        # n_rows, n_columns = 0, 0
    channels = np.zeros(n_channels_max, dtype=bool)
    channels[:n_channels] = True

    # n_channels = np.sum(channels).item()
    fs = config['processor'].getint('fs')
    channel_index = channels.tolist()
    channel_index += [
        sound_channel_index,
        timestamp_channel_index,
        control_channel_index,
        stimulus_channel_index
    ]
    channel_index = np.asarray(channel_index, dtype=int)
    channels_bad = np.zeros(n_channels, dtype=bool)
    # print(channels_bad)
    channel_names = ['channel_{}'.format(i + 1) for i in range(n_channels)]
    channel_names += ['sound', 'timestamp', 'control', 'stimulus']
    dataset_width = len(channel_names)

    # print(n_channels)
    processor_config = ProcessorConfig(
        channels=channels,
        n_channels=n_channels,
        n_channels_grid=n_channels_grid,
        n_rows=n_rows,
        n_columns=n_columns,
        grid_type=grid_type,
        fs=fs,
        channel_index=channel_index,
        channels_bad=channels_bad,
        channel_names=channel_names,
        dataset_width=dataset_width,
    )
    processor_config.set_events_handlers(em)


    # recorder_config = RecorderConfig(
    #     fs=fs,
    #     channel_index=channel_index,
    #     channels_bad=channels_bad,
    #     channel_names=channel_names,
    #     dataset_width=dataset_width,
    # )
    # recorder_config.set_events_handlers(em)



    envelope_fmin = config['decoder'].getint('envelope_fmin')
    envelope_fmax = config['decoder'].getint('envelope_fmax')
    envelope_fstep = config['decoder'].getint('envelope_fstep')
    decoder_config = DecoderConfig(
        envelope_fmin=envelope_fmin,
        envelope_fmax=envelope_fmax,
        envelope_fstep=envelope_fstep
    )
    decoder_config.set_events_handlers(em)

    downsample = config['visualizer'].getboolean('downsample')
    fs_downsample = config['visualizer'].getint('fs_downsample')
    n_samples_timeseries_sec = config['visualizer'].getfloat('n_samples_timeseries_sec')
    if downsample:
        n_samples_timeseries = int(fs_downsample * n_samples_timeseries_sec)
    else:
        n_samples_timeseries = int(fs * n_samples_timeseries_sec)
    n_samples_timeseries_sound_sec = config['visualizer'].getfloat('n_samples_timeseries_sound_sec')
    if downsample:
        n_samples_timeseries_sound = int(fs_downsample * n_samples_timeseries_sound_sec)
    else:
        n_samples_timeseries_sound = int(fs * n_samples_timeseries_sound_sec)


    vis_view = config['visualizer']['vis_view']
    notch_q = config['visualizer'].getfloat('notch_q')
    notch_n = config['visualizer'].getint('notch_n')
    ecog_hpf = config['visualizer'].getfloat('ecog_hpf')
    ecog_lpf = config['visualizer'].getfloat('ecog_lpf')
    hg_ecog_bpfl = config['visualizer'].getfloat('hg_ecog_bpfl')
    hg_ecog_bpfh = config['visualizer'].getfloat('hg_ecog_bpfh')
    log_transform = config['visualizer'].getboolean('log_transform')
    hg_ecog_sf = config['visualizer'].getfloat('hg_ecog_sf')

    spec_ecog_low = config['visualizer'].getint('spec_ecog_low')
    spec_ecog_high = config['visualizer'].getint('spec_ecog_high')
    spec_hg_ecog_low = config['visualizer'].getint('spec_hg_ecog_low')
    spec_hg_ecog_high = config['visualizer'].getint('spec_hg_ecog_high')
    spec_window_size = config['visualizer'].getint('spec_window_size')
    spec_decay = config['visualizer'].getfloat('spec_decay')

    ecog_notch = config['visualizer'].getboolean('ecog_notch')
    ecog_highpass_filter = config['visualizer'].getboolean('ecog_highpass_filter')
    ecog_lowpass_filter = config['visualizer'].getboolean('ecog_lowpass_filter')

    visualizer_config = VisualizerConfig(
        downsample=downsample,
        fs_downsample=fs_downsample,
        n_samples_timeseries_sec=n_samples_timeseries_sec,
        n_samples_timeseries=n_samples_timeseries,
        n_samples_timeseries_sound_sec=n_samples_timeseries_sound_sec,
        n_samples_timeseries_sound=n_samples_timeseries_sound,
        vis_view=vis_view,
        notch_q=notch_q,
        notch_n=notch_n,
        ecog_hpf=ecog_hpf,
        ecog_lpf=ecog_lpf,
        hg_ecog_bpfl=hg_ecog_bpfl,
        hg_ecog_bpfh=hg_ecog_bpfh,
        log_transform=log_transform,
        hg_ecog_sf=hg_ecog_sf,
        spec_ecog_low=spec_ecog_low,
        spec_ecog_high=spec_ecog_high,
        spec_hg_ecog_low=spec_hg_ecog_low,
        spec_hg_ecog_high=spec_hg_ecog_high,
        spec_window_size=spec_window_size,
        spec_decay=spec_decay,
        ecog_notch=ecog_notch,
        ecog_highpass_filter=ecog_highpass_filter,
        ecog_lowpass_filter=ecog_lowpass_filter,
    )
    visualizer_config.set_events_handlers(em)

    conf = Config(
        patient_info=patient_info_config,
        general=general_config,
        paths=path_config,
        experiment=experiment_config,
        processor=processor_config,
        receiver=receiver_config,
        # recorder=recorder_config,
        decoder=decoder_config,
        visualizer=visualizer_config
    )

    # em.register_event('update config.patient_info.patient_name')
    # em.register_event('update config.general.debug_mode')
    # em.register_event('update config.receiver.amplifier')
    # em.register_event('update config.receiver.amplifier_ip')
    # em.register_event('update config.receiver.fs')
    # em.register_event('update config.receiver.channels')
    # em.register_event('update config.recorder.channels_bad')

    em.register_handler('save_config', conf.handle_event_config_save)
    return conf


def write_config_file(path, conf):
    config = configparser.ConfigParser()

    config['patient_info'] = {}
    config['patient_info']['patient_name'] = conf.patient_info.patient_name
    config['patient_info']['patient_date'] = conf.patient_info.patient_date

    config['general'] = {}
    # config['general']['control_type'] = str(conf.general.control_type)

    config['paths'] = {}
    config['paths']['data_path'] = str(conf.paths.data_path)

    config['experiment'] = {}
    config['experiment']['stimulus_type'] = str(conf.experiment.stimulus_type)
    config['experiment']['n_stimulus'] = str(conf.experiment.n_stimulus)
    # config['experiment']['n_control'] = str(conf.experiment.n_control)
    config['experiment']['stimulus_time'] = str(conf.experiment.stimulus_time)
    config['experiment']['switch_time'] = str(conf.experiment.switch_time)
    # config['experiment']['single_sound_time'] = str(conf.experiment.single_sound_time)
    # config['experiment']['between_picture_time'] = str(conf.experiment.between_picture_time)
    # config['experiment']['between_word_time'] = str(conf.experiment.between_word_time)
    # config['experiment']['between_sound_time'] = str(conf.experiment.between_sound_time)
    # config['experiment']['use_random_intervals'] = str(conf.experiment.use_random_intervals)
    # config['experiment']['random_interval_length'] = str(conf.experiment.random_interval_length)
    # config['experiment']['shuffle_stimulus'] = str(conf.experiment.shuffle_stimulus)
    # config['experiment']['stimulus_type'] = str(conf.experiment.stimulus_type)

    config['receiver'] = {}
    config['receiver']['amplifier'] = str(conf.receiver.amplifier)
    config['receiver']['amplifier_ip'] = str(conf.receiver.amplifier_ip)
    config['receiver']['fs'] = str(conf.receiver.fs)
    config['receiver']['cache_size'] = str(conf.receiver.cache_size)
    config['receiver']['cache_width'] = str(conf.receiver.cache_width)
    config['receiver']['n_channels_max'] = str(conf.receiver.n_channels_max)
    config['receiver']['sound_channel_index'] = str(conf.receiver.sound_channel_index)
    config['receiver']['timestamp_channel_index'] = str(conf.receiver.timestamp_channel_index)
    config['receiver']['control_channel_index'] = str(conf.receiver.control_channel_index)
    config['receiver']['stimulus_channel_index'] = str(conf.receiver.stimulus_channel_index)

    # config['recorder'] = {}
    # config['recorder']['save_path'] = str(conf.recorder.save_path)

    config['decoder'] = {}
    config['decoder']['envelope_fmin'] = str(conf.decoder.envelope_fmin)
    config['decoder']['envelope_fmax'] = str(conf.decoder.envelope_fmax)
    config['decoder']['envelope_fstep'] = str(conf.decoder.envelope_fstep)

    config['visualizer'] = {}
    with open(path, 'w') as configfile:
        config.write(configfile)


# parse the command line arguments
def parse_argv(config, argv):
    # debug mode, uses lsl generator instead if amplifier data
    if '-debug' in argv:
        config['general']['debug_mode'] = 'true'
    elif '-objects' in argv:
        config['general']['objects_mode'] = 'true'
    elif '-actions' in argv:
        config['general']['actions_mode'] = 'true'
    elif '-questions' in argv:
        config['general']['questions_mode'] = 'true'
    else:
        config['general']['objects_mode'] = 'true'


if __name__ == '__main__':
    # config_init()
    from event_manager import EventManager

    em = EventManager()
    path = '../config/config_default.ini'
    config = read_config_file(path=path)
    conf = parse_config(em, config)

    conf.ui._update_window_x(200)
    print(conf.ui.window_x)
    print(conf.ui._update_window_x)

    em.trigger('update config.receiver.fs', 123)
    conf.receiver._update_fs(100)