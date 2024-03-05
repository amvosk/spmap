import numpy as np
import vispy
from vispy import app, scene
from vispy.geometry import Rect
from PyQt6 import QtCore
import copy
from functools import partial


class SoundCanvas:
    line_scale = 0.1
    line_scale_coef = 1.5
    line_space = 30
    line_space_coef = 1.5

    def __init__(self, em, config):
        # Create a canvas and viewbox
        self.em = em
        self.config = config

        self.config.decoder.use_sound = True

        self.n_samples = self.config.visualizer.n_samples_timeseries_sound
        self.courser = 0
        self.use_sound = self.config.decoder.use_sound
        self.points = np.zeros((self.n_samples, 2))
        self.points[:, 0] = np.linspace(0, 1, self.n_samples)

        self.canvas = scene.SceneCanvas(keys='interactive',  bgcolor = (0, 0, 0, 1))  # , size=(self.canvas_width, self.canvas_height))
        self.view = self.canvas.central_widget.add_view()
        self.width, self.height = self.canvas.size

        rect_ecog = Rect(0, 0, self.width, self.height)
        self.view.camera = scene.PanZoomCamera(rect=rect_ecog, interactive=False)
        self.view.camera.padding = 0

        self.line = None
        self._create_line()
        self.em.register_handler('update config.decoder.use_sound', self._update_parametes)
        self.em.register_handler('update config.visualizer.n_samples_plot_sound', self._update_parametes)
        self.canvas.events.mouse_wheel.connect(self.on_mouse_wheel)


    def _update_parametes(self, args):
        self.n_samples = self.config.visualizer.n_samples_plot_sound
        self.use_sound = self.config.decoder.use_sound
        self.courser = 0
        self.points = np.zeros((self.n_samples, 2))
        self.points[:, 0] = np.linspace(0, 1, self.n_samples)
        self._create_line()

    def _create_line(self):
        offset = self.height // 2
        self.view.camera.set_range(x=(0, self.width), y=(0, self.height), margin=0)

        self.line = scene.Line(self.points, parent=self.view.scene, color='white')
        self.line.transform = scene.STTransform(
            translate=(0, offset), scale=(self.width, self.line_scale)
        )
        self.line._visible = self.use_sound
        self.canvas.update()


    def update_data(self, data):
        if self.courser + data.shape[0] < self.n_samples:
            courser_new = self.courser + data.shape[0]
            self.points[self.courser:courser_new, 1] = data
            self.courser = courser_new
        elif data.shape[0] > self.n_samples:
            self.points[:, 1] = data[-self.n_samples:]
            self.courser = 0
        elif self.courser + data.shape[0] > self.n_samples:
            courser_new = self.courser + data.shape[0] - self.n_samples
            data_part1 = data[:self.n_samples - self.courser]
            data_part2 = data[self.n_samples - self.courser:]
            self.points[self.courser:, 1] = data_part1
            self.points[:courser_new, 1] = data_part2
        elif self.courser + data.shape[0] == self.n_samples:
            self.points[self.courser:, 1] = data
            self.courser = 0

        self.line.set_data(self.points)
        self.canvas.update()


    def on_mouse_wheel(self, event):
        if event.delta[1] > 0:
            self.line_scale *= self.line_scale_coef
        else:
            self.line_scale /= self.line_scale_coef
        self.line.transform.scale = (self.width, self.line_scale)
        self.canvas.update()


def callback_function(config, queue, canvas):
    while True:
        if not queue.empty():
            chunk = queue.get()
            data = chunk[:, :config.receiver.n_channels_max]
            canvas.update_data(data)


if __name__ == '__main__':
    pass
