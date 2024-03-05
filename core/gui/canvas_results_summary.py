import numpy as np
# import vispy
import os
from queue import Empty
from vispy import app, scene
# from PyQt6 import QtGui, QtWidgets
from vispy.geometry import Rect
# from PyQt6 import QtCore
from vispy.io import load_data_file, read_png
import vispy.io.image

import copy
from functools import partial
from PIL import Image
import time
# import colorsys
import colorsys
from vispy.color import Color



import numpy as np
from vispy import scene
from vispy.scene import Text
from vispy.scene.visuals import Ellipse
from vispy.visuals.transforms import STTransform
from PyQt6.QtCore import QTimer

class CellContent:
    def __init__(
            self, x_pos, y_pos,
            circle_radius, parent,
            channel_label_text, font_size,
            magnitude, confidence, visible
    ):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.circle_radius = circle_radius
        self.channel_label_text = channel_label_text
        self.font_size = font_size
        self.visible = visible
        self.magnitude = 0
        self.confidence = 0


        color_rgb=Color(self._hsv_to_rgb(self._results_to_hsv(self.magnitude, self.confidence))).rgb


        self.magnitude_circle = Ellipse(center=(self.x_pos, self.y_pos), radius=self.circle_radius, color=color_rgb, parent=parent)
        self.magnitude_circle.visible = False
        self.channel_label = Text(self.channel_label_text, bold=True, font_size=self.font_size, pos=(self.x_pos, self.y_pos + self.font_size * 0), color='white', parent=parent)
        self.channel_label.visible = self.visible

    def update_position(self, x_pos, y_pos):
        self.x_pos, self.y_pos = x_pos, y_pos
        self.magnitude_circle.center = (x_pos, y_pos)
        self.channel_label.pos = (x_pos, y_pos)

    def update_text(self, text):
        self.channel_label_text = text

    def update_size(self, font_size, circle_radius):
        self.circle_radius = circle_radius
        self.font_size = font_size
        self.magnitude_circle.radius = circle_radius
        self.channel_label.font_size = font_size

    def update_color(self, magnitude, confidence):
        self.magnitude = magnitude
        self.confidence = confidence
        color_rgb = Color(self._hsv_to_rgb(self._results_to_hsv(self.magnitude, self.confidence))).rgb
        self.magnitude_circle.color = color_rgb

    def _results_to_hsv(self, magnitude, confidence):
        blue_hue = 240
        red_hue = 0
        hue = blue_hue + ((red_hue - blue_hue) % 360) * magnitude
        saturation = confidence ** 2
        value = confidence ** 2
        return hue, saturation, value

    def _hsv_to_rgb(self, hsv):
        h, s, v = hsv
        return colorsys.hsv_to_rgb(h / 360, s, v)


    def make_visible(self, visibility=True):
        self.visible = visibility
        self.magnitude_circle.visible = visibility
        self.channel_label.visible = visibility




class ResultsSummaryCanvasWrapper:
    def __init__(self, em, config, size=(600, 800)):
        self.em = em
        self.config = config

        self.canvas = scene.SceneCanvas(keys='interactive')
        self.canvas.title = 'Summary'

        self.grid = self.canvas.central_widget.add_grid()

        for row in range(self.config.processor.n_rows):
            for col in range(self.config.processor.n_columns):
                view = self.grid.add_view(row=row, col=col)
                view.bgcolor = "#000000"

        self.circle_radius_base = 50
        self.font_size_base = 20
        self.window_scale = min(self.grid.size)

        self.cell_contents = None
        self.draw_grid()

        self.em.register_handler('update config.processor.channels', self._handler_update_channels)
        # self.em.register_handler('update config.processor.channels', self._cell_set_visible)
        self.em.register_handler('update config.processor.channels_bad', self._cell_set_visible)

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.adjust_visuals)
        self.resize_delay = 500  # Delay in milliseconds
        self.canvas.events.resize.connect(self.on_resize)

    def _handler_update_channels(self, args=None):
        self.cell_contents = None
        self.canvas.central_widget.remove_widget(self.grid)
        self.grid = self.canvas.central_widget.add_grid()
        for row in range(self.config.processor.n_rows):
            for col in range(self.config.processor.n_columns):
                view = self.grid.add_view(row=row, col=col)
                view.bgcolor = "#000000"
        self.draw_grid()
        self._cell_set_visible()
        self.canvas.update()





    def _cell_set_visible(self, args=None):
        n_rows, n_columns = self.config.processor.n_rows, self.config.processor.n_columns
        channels_bad = np.copy(self.config.processor.channels_bad)
        # print(channels_bad)
        grid_channels_bad = self.vec2grid(channels_bad, n_rows, n_columns)
        for row in range(n_rows):
            for col in range(n_columns):
                if self.cell_contents[row][col] is not None:
                    visibility = grid_channels_bad[row, col]
                    if visibility == self.cell_contents[row][col].visible:
                        self.cell_contents[row][col].make_visible(not visibility)
        self.canvas.update()

    def on_resize(self, event):
        self.resize_timer.start(self.resize_delay)

    def adjust_visuals(self):
        n_rows, n_columns = self.config.processor.n_rows, self.config.processor.n_columns
        cell_size = self.grid.size[0] / n_columns, self.grid.size[1] / n_rows
        current_window_scale = min(self.grid.size) / self.window_scale
        for row in range(n_rows):
            for col in range(n_columns):
                if self.cell_contents[row][col] is not None:
                    self.cell_contents[row][col].update_position(0.5 * cell_size[0], 0.5 * cell_size[1])
                    self.cell_contents[row][col].update_size(self.font_size_base * current_window_scale, self.circle_radius_base * current_window_scale)
                    self.cell_contents[row][col].make_visible(True)

    def change_results(self, magnitude, confidence):
        n_rows, n_columns = self.config.processor.n_rows, self.config.processor.n_columns
        grid_magnitude = self.vec2grid(magnitude, n_rows, n_columns)
        grid_confidence = self.vec2grid(confidence, n_rows, n_columns)

        for row in range(n_rows):
            for col in range(n_columns):
                if self.cell_contents[row][col] is not None:
                    self.cell_contents[row][col].update_color(grid_magnitude[row, col], grid_confidence[row, col])
        self.canvas.update()


    def vec2grid(self, vec, n_rows, n_columns):
        # assert vec.shape[0] == n_rows * n_columns
        if vec.shape[0] < n_rows * n_columns:
            vec = np.concatenate([vec, np.nan * np.ones((n_rows * n_columns - vec.shape[0], *vec.shape[1:]))])
        axis = (1, 0, *(np.arange(len(vec.shape))[1:] + 1))
        vec_ = vec.reshape((n_columns, n_rows, *vec.shape[1:]))[::-1]
        grid = np.transpose(vec_, axes=axis)
        return grid


    def draw_grid(self, args=None):
        n_rows, n_columns = self.config.processor.n_rows, self.config.processor.n_columns
        channel_flags = np.concatenate([np.ones(self.config.processor.n_channels, dtype=bool), np.zeros(n_rows*n_columns - self.config.processor.n_channels, dtype=bool)])
        channel_flags = self.vec2grid(channel_flags, n_rows, n_columns)
        channel_labels = np.arange(1, n_rows * n_columns + 1)
        channel_grid = self.vec2grid(channel_labels, n_rows, n_columns)
        cell_size = self.grid.size[0] / n_columns, self.grid.size[1] / n_rows
        current_window_scale = min(self.grid.size) / self.window_scale

        self.cell_contents = [[None for _ in range(n_columns)] for _ in range(n_rows)]
        for row in range(n_rows):
            for col in range(n_columns):
                if not np.isnan(channel_flags[row, col]):
                    self.cell_contents[row][col] = CellContent(
                        x_pos=0.5 * cell_size[0],
                        y_pos=0.5 * cell_size[1],
                        circle_radius=self.circle_radius_base * current_window_scale,
                        parent=self.grid[row, col],
                        channel_label_text=str(channel_grid[row, col]),
                        font_size=self.font_size_base * current_window_scale,
                        magnitude=0,
                        confidence=0,
                        visible=False,
                    )
                else:
                    self.cell_contents[row][col] = None



if __name__ == '__main__':
    pass
