import sys, os, time
import numpy as np
import h5py

sys.path.insert(0, '../core/')
sys.path.insert(0, '../config/')
from config import read_config_file, parse_config
from PyQt6 import QtWidgets
# from PyQt6 import QtWidgets.QSizePolicy
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSizePolicy
from event_manager import EventManager
from experiment import Experiment
from gui.canvas_pictures import PicturesCanvas
from vispy import app
import numpy as np
from functools import partial
from PyQt6.QtCore import QTimer
from PyQt6 import QtCore


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()

        self.setWindowTitle('VisPy in PyQt6')
        self.setGeometry(100, 100, 800, 800)
        widget = QWidget()
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        config_file_path = '../config/config_default.ini'
        config_ini = read_config_file(config_file_path)

        em = EventManager()
        config = parse_config(em, config_ini)

        self.canvas_pictures = PicturesCanvas(em, config)

        layout.addWidget(self.canvas_pictures.canvas.native)

        self.experiment = Experiment(config, em)
        self.experiment.start()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(lambda : self.push_pictures(self.experiment.queue_output, self.canvas_pictures.update_image))
        self.timer.start(1)

    def push_pictures(self, queue, update_image):
        if (queue.empty()): return
        data = queue.get(block=False)
        update_image(data)


if __name__ == '__main__':

    gui = QtWidgets.QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(gui.exec())



