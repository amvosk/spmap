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
from gui.canvas_results_summary import ResultsSummaryCanvasWrapper
from vispy import app
import numpy as np
from functools import partial
from PyQt6.QtCore import QTimer


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
        self.canvas = ResultsSummaryCanvasWrapper(em, config)
        self.canvas.canvas.native.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        self.resize_timer = QTimer()
        # self.resize_timer.setSingleShot(False)
        self.resize_timer.timeout.connect(self.change_results)
        self.resize_timer.start(2000)
        # widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.canvas.canvas.show()


    def change_results(self):
        magnitude = np.random.uniform(0,1,20)
        confidence = np.random.uniform(0,1,20)
        confidence = np.ones(20) * 0.9
        confidence[np.asarray([8,9,10,13])] = 0.1

        magnitude = np.ones(20) * 0.1
        magnitude[18] = 0.9
        tic = time.perf_counter()
        self.canvas.change_results(magnitude, confidence)
        toc = time.perf_counter()
        print(toc - tic)

if __name__ == '__main__':

    gui = QtWidgets.QApplication(sys.argv)
    w = MyWindow()
    sys.exit(gui.exec())

    # config_file_path = '../config/config_default.ini'
    # config_ini = read_config_file(config_file_path)
    # em = EventManager()
    # config = parse_config(em, config_ini)
    #
    # canvas = ResultsSummaryCanvasWrapper(em, config)
    # canvas.canvas.show()

    # values = np.random.uniform(size=(20, 10))

    # def update(canvas, values, event):
    #     print(event.iteration)
    #     canvas.update_grid(values[..., event.iteration % values.shape[-1]])
    #
    # timer = app.Timer(interval=1.0, connect=partial(update, canvas, values), start=True)
    # canvas.app.run()


