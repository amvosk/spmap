import sys

sys.path.insert(0, '../core/')
from config import read_config_file, parse_config
from event_manager import EventManager

if __name__ == '__main__':
    config_file_path = '../config/config_default.ini'
    config_ini = read_config_file(config_file_path)

    em = EventManager()
    config = parse_config(em, config_ini)

    for field, value in vars(config).items():
        print('Field:', field)
        for f, v in vars(value).items():
            print(f, v)
        print('\n')
