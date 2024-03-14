import sys, time


# sys.path.insert(0, '../config/')
# sys.path.insert(0, '../generation/')
# from generator import GeneratorLSL

from config import read_config_file, parse_config#, LocalConfig
from event_manager import EventManager

from interface import MainWindow
from PyQt6 import QtWidgets


def main():
    em = EventManager()
    config_file_default_path = '../config/config_default.ini'
    # config_file_path = '../config/config.ini'
    config_ini = read_config_file(config_file_default_path)
    config = parse_config(em, config_ini)

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(config, em)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
