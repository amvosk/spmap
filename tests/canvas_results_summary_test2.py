import math
import sys

from vispy import gloo, app

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout

sys.path.insert(0, '../core/')
sys.path.insert(0, '../config/')
from config import read_config_file, parse_config
from event_manager import EventManager
from gui.canvas_results_summary2 import Canvas, ResultsSummaryCanvas
from functools import partial
import numpy as np

# app.use_app("pyqt6")


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
        self.canvas = ResultsSummaryCanvas(em, config)

        # canvas.canvas.show()

        # values = np.random.uniform(size=(20, 10))

        # def update(canvas, values, event):
        #     print(event.iteration)
        #     canvas.update_grid(values[..., event.iteration % values.shape[-1]])
        #
        # timer = app.Timer(interval=1.0, connect=partial(update, canvas, values), start=True)

        # self.canvas = Canvas()

        layout.addWidget(self.canvas.native)

        values = np.random.uniform(size=(20, 10))
        # def update(canvas, values, event):
        #     print(event.iteration)
        #     canvas.update_grid(values[..., event.iteration % values.shape[-1]])
        self.timer = app.Timer(interval=1.0, connect=lambda event: self.canvas.update_grid(values[..., event.iteration % values.shape[-1]]), start=True)

        self.show()

if __name__ == "__main__":
    gui = QtWidgets.QApplication(sys.argv)
    w = MyWindow()
    # w.show()
    # app.run()
    sys.exit(gui.exec())
