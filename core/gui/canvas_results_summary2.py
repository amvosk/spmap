import numpy as np
# import vispy
# import os
# from queue import Empty
# # from vispy import app, scene
# from PyQt6 import QtGui, QtWidgets
# from vispy.geometry import Rect
# from PyQt6 import QtCore
# from vispy.io import load_data_file, read_png
# import vispy.io.image

# import copy
# from functools import partial
# from PIL import Image
# import time

# from vispy import scene
# from vispy.app import Timer
# from vispy.scene import Text
# from vispy.scene.visuals import Ellipse
# from vispy.visuals.transforms import STTransform
# from vispy.visuals.ellipse  import EllipseVisual
from vispy import app, gloo, visuals
# from functools import partial
import math
from vispy.visuals.transforms import STTransform

from vispy import gloo, app
# app.use_app("pyqt6")
#
#
# class Canvas(app.Canvas):
#     def __init__(self, *args, **kwargs):
#         app.Canvas.__init__(self, *args, **kwargs)
#         self._timer = app.Timer("auto", connect=self.on_timer, start=True)
#         self.tick = 0
#
#     def on_draw(self, event):
#         gloo.clear(color=True)
#
#     def on_timer(self, event):
#         self.tick += 1 / 60.0
#         c = abs(math.sin(self.tick))
#         gloo.set_clear_color((c, c, c, 1))
#         self.update()
#
#
# class ResultsSummaryCanvas(app.Canvas):
#     def __init__(self, em, config):
#         app.Canvas.__init__(self, title='Custom Visualization', size=(800, 600), keys='interactive')
#         self.em = em
#         self.config = config
#
#         self.circle_radius = 0.15
#         # self.flip_transform = STTransform(scale=(1, -1), translate=(0, 600))
#
#         # self.magnitude_circles = []
#         # self.channel_labels = []
#         # self.quantile_circles = []
#         self.grid = []
#         self.generate_grid()
#         self.update()
#
#     def vec2grid(self, vec, n_rows, n_columns):
#         assert vec.shape[0] == n_rows * n_columns
#         axis = (1, 0, *(np.arange(len(vec.shape))[1:] + 1))
#         vec_ = vec.reshape((n_columns, n_rows, *vec.shape[1:]))[::-1]
#         grid = np.transpose(vec_, axes=axis)
#         return grid
#
#
#     def generate_grid(self):
#         # n_rows, n_columns = 5, 4
#         # grid_width, grid_height = 800, 600
#         # cell_width = grid_width / n_columns
#         # cell_height = grid_height / n_rows
#
#         electrode_type = 'grid 4x5'
#         if electrode_type == 'grid 4x5':
#             channel_names = np.asarray([i for i in range(1, 20+1)])
#             n_rows = 5
#             n_columns = 4
#             channel_grid = self.vec2grid(channel_names, n_rows, n_columns)
#
#         grid_width, grid_height = 800, 600
#         cell_width = grid_width / n_columns
#         cell_height = grid_height / n_rows
#
#         class GridCell:
#             def __init__(self, row, col, grid_width, grid_height, n_columns, n_rows, circle_radius, channel_name):
#
#                 self.x_pos = (col + 0.5) * cell_width / grid_width * 2 - 1
#                 self.y_pos = (row + 0.5) * cell_height / grid_height * 2 - 1
#                 self.magnitude_circle = visuals.EllipseVisual(center=(self.x_pos, self.y_pos), radius=(circle_radius, circle_radius), color=(0.8, 0.2, 0.2, 1), border_color=(0, 0, 0, 1), border_width=2)
#                 self.channel_label = visuals.TextVisual(text=f'{channel_name}', pos=(self.x_pos, self.y_pos), font_size=10.0, color=(1, 1, 1, 1))
#                 self.channel_label.transforms.dpi = 1
#                 self.quantile_circles = []
#                 for r in [0.25, 0.5, 0.75, 1]:
#                     quantile_circle = visuals.EllipseVisual(center=(self.x_pos, self.y_pos), radius=circle_radius * r, color=(0, 0, 0, 0), border_color=(1, 0.5, 0, 0.8), border_width=2)
#                     self.quantile_circles.append(quantile_circle)
#
#         self.grid = []
#         for row in range(n_rows):
#             self.grid.append([])
#             for col in range(n_columns):
#                 grid_cell = GridCell(row, col, grid_width, grid_height, n_columns, n_rows, self.circle_radius * channel_grid[row, col] / 20, str(channel_grid[row, col]))
#                 self.grid[row].append(grid_cell)
#
#
#
#                 # x_pos = (col + 0.5) * cell_width / grid_width * 2 - 1
#                 # y_pos = (row + 0.5) * cell_height / grid_height * 2 - 1
#
#                 # magnitude_circle = visuals.EllipseVisual(center=(x_pos, y_pos), radius=(self.circle_radius * channel_grid[row,col]/20, self.circle_radius *channel_grid[row,col]/20), color=(0.8, 0.2, 0.2, 1), border_color=(0, 0, 0, 1), border_width=2)
#                 # magnitude_circle.transforms = STTransform(scale=(1, -1), translate=(0, grid_height))
#                 # self.magnitude_circles.append(magnitude_circle)
#
#                 # channel_label = visuals.TextVisual(text=f'{channel_grid[row,col]}', pos=(x_pos, y_pos), color=(1, 1, 1, 1))
#                 # channel_label.transforms = flip_transform
#                 # channel_label.transforms.dpi = 1
#                 # vp = (0, 0, self.physical_size[0], self.physical_size[1])
#                 # channel_label.transforms.configure(canvas=self, viewport=vp)
#                 # channel_label.font_size = 10.0
#                 # self.channel_labels.append(channel_label)
#
#                 # for r in [0.25, 0.5, 0.75, 1]:
#                 #     quantile_circle = visuals.EllipseVisual(center=(x_pos, y_pos), radius=self.circle_radius * r, color=(0, 0, 0, 0), border_color=(1, 0.5, 0, 0.8), border_width=2)
#                 #     self.quantile_circles.append(quantile_circle)
#
#     # def on_resize(self, event):
#     #     viewport = (0, 0, self.physical_size[0], self.physical_size[1])
#         # for visual in self.magnitude_circles:
#         #     visual.transforms.configure(canvas=self, viewport=viewport)
#
#     def on_draw(self, ev):
#         # gloo.clear(color=True)
#         gloo.set_clear_color('black')
#         gloo.clear()
#         # for vis in (self.magnitude_circles + self.channel_labels + self.quantile_circles):
#         #     vis.draw()
#         for grid_cell_row in self.grid:
#             for grid_cell in grid_cell_row:
#                 grid_cell.magnitude_circle.draw()
#                 grid_cell.channel_label.draw()
#                 for x in grid_cell.quantile_circles:
#                     x.draw()
#
#
#     def update_grid(self, magnitude):
#         # print(magnitude.shape)
#         # Assuming magnitude is an array with one value per visual in the grid
#         # for magnitude_circle, mag in zip(self.magnitude_circles, magnitude):
#         #     magnitude_circle.radius = self.circle_radius * mag
#             # Here you would adjust visual properties based on magnitude
#             # For example, adjusting the color based on magnitude
#             # pass
#         # magnitude = np.asarray([i for i in range(1, 20+1)]) / 20
#         magnitude_grid = self.vec2grid(magnitude, len(self.grid), len(self.grid[0]))
#         for row in range(len(self.grid)):
#             for col in range(len(self.grid[row])):
#                 self.grid[row][col].magnitude_circle.radius = self.circle_radius * magnitude_grid[row, col]
#         self.update()
#
#
#
# if __name__ == '__main__':
#     pass
