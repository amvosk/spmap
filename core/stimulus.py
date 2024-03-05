import math
import pandas as pd
import numpy as np

from config import read_config_file, parse_config
from event_manager import EventManager


class Stimulus:
    def __init__(self, config, em):
        self.config = config
        self.em = em
        self.df_nouns = self._load_df('nouns.xls')

    def _load_df(self, df_filename):
        xl_file = pd.ExcelFile(self.config.paths.resource_path / df_filename)
        df = xl_file.parse()
        df.set_index('index', inplace=True)
        return df

    def _get_top_n_stimulus(self):
        n_stimulus = self.config.experiment.n_stimulus
        difficulty = self.config.experiment.stimulus_difficulty
        stimulus_feature = self.config.experiment.stimulus_feature
        stimulus_type = self.config.experiment.stimulus_type
        if stimulus_type in ['objects', 'words', 'sounds']:
            df = self.df_nouns
        elif stimulus_type in ['actions']:
            df = self.df_nouns
        else:
            df = self.df_nouns

        if stimulus_feature == 'subjective_complexity':
            df_sorted = df.sort_values(
                ['picture complexity subjective, mean'],
                ascending=[difficulty == 'easy']
            )
        elif stimulus_feature == 'picture_familiarity':
            df_sorted = df.sort_values(
                ['picture familiarity, mean'],
                ascending=[difficulty != 'easy']
            )
        elif stimulus_feature == 'noun_acquisition_age':
            df_sorted = df.sort_values(
                ['noun acquisition age, mean'],
                ascending=[difficulty == 'easy']
            )
        elif stimulus_feature == 'noun_imageability':
            df_sorted = df.sort_values(
                ['noun imageability, mean'],
                ascending=[difficulty != 'easy']
            )
        elif stimulus_feature == 'noun_picture_agreement':
            df_sorted = df.sort_values(
                ['noun-picture agreement, mean'],
                ascending=[difficulty != 'easy']
            )
        elif stimulus_feature == 'noun_frequency':
            df_sorted = df.sort_values(
                ['noun frequency'],
                ascending=[difficulty != 'easy']
            )
        else:
            df_sorted = df
        df_stimulus = df_sorted.head(n_stimulus).sort_index()
        values = df_stimulus.index.values
        # print(values)
        if self.config.experiment.shuffle_stimulus:
            np.random.seed(0)
            np.random.shuffle(values)
        return values

    def get_splits(self):
        values = self._get_top_n_stimulus()
        splits = []
        counter = 0
        for i in self.config.experiment.n_stimulus_per_split:
            counter_next = counter + i
            values_split = values[counter:counter_next]
            splits.append(values_split)
            counter = counter_next
        return splits


if __name__ == '__main__':

    em = EventManager()
    config_file_default_path = '../config/config_default.ini'
    config_ini = read_config_file(config_file_default_path)
    conf = parse_config(em, config_ini)

    pictures = Pictures(conf, em)
    print(pictures._get_top_n_stimulus())