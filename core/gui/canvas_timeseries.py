import numpy as np
import vispy
from vispy import app, scene
from vispy.geometry import Rect
from PyQt6 import QtCore
import copy
from functools import partial


class LocalConfig:
    def __init__(self):
        self.line_scale = 0.003
        self.line_scale_coef = 1.5
        self.line_space = 30
        self.line_space_coef = 1.5
        self.width = None
        self.height = None
        self.offsets = None

class TimeSeriesCanvas:
    camera = None

    def __init__(self, em, config):
        # Create a canvas and viewbox
        self.em = em
        self.config = config
        self.config_local = LocalConfig()
        self.courser = 0
        self.line_color = 'white'

        self.canvas = scene.SceneCanvas(keys='interactive', bgcolor = (0, 0, 0, 1))  # , size=(self.canvas_width, self.canvas_height))
        self._update_plot_params()

        rect_ecog = Rect(0, 0, self.config_local.width, self.config_local.height)
        self.camera = scene.PanZoomCamera(rect=rect_ecog, interactive=False)
        self.camera.padding = 0

        self.view_types = ['ECoG', 'hgECoG', 'hgA']

        self.views = {}
        for view_type in self.view_types:
            self.views[view_type] = View(self.config, self.config_local, self.canvas, view_type, self.camera, self.line_color)
        self._update_vis_view()
        self.em.register_handler('update config.visualizer.vis_view', self._update_vis_view)
        self.em.register_handler('update config.visualizer.vis_view', self._update_lines_location)

        self.em.register_handler('update config.visualizer parameters', self._draw_channels)
        self.em.register_handler('update config.processor.channels', self._draw_channels)
        self.em.register_handler('update config.processor.channels_bad', self._channels_set_visible)

        self.em.register_handler('gui.canvas_timeseries.update_data', self.update_data)

        self.canvas.events.mouse_wheel.connect(self.on_mouse_wheel)


    def _update_plot_params(self, args=None):
        self.config_local.width, _ = self.canvas.size
        height_old = self.config_local.height
        self.config_local.height = (self.config.processor.n_channels + 1) * self.config_local.line_space
        if self.config_local.height != height_old:
            self.em.trigger('update brain_checkbox_height', self.config_local.height)
        offsets = self.config_local.line_space * (np.arange(self.config.processor.n_channels) + 1)
        self.config_local.offsets = offsets[::-1]
        # self.em.trigger('update canvas.timeseries.height', self.config_local.height)
        # print(self.config_local.width, self.config_local.height, self.config_local.offsets)

    def _update_vis_view(self, args=None):
        for view_type, view in self.views.items():
            view.disable()
        self.views[self.config.visualizer.vis_view].enable()
        self.canvas.update()

    def _draw_channels(self, args=None):
        self._update_plot_params()
        self.camera.set_range(x=(0, self.config_local.width), y=(0, self.config_local.height), margin=0)
        for view_type, view in self.views.items():
            view.draw_lines(self.line_color)
        # self.em.trigger('update brain_checkbox_height', self.config_local.height)
        self.canvas.update()

    def _channels_set_visible(self, args=None):
        for view_type, view in self.views.items():
            view.update_lines_visibility()
        self.canvas.update()


    def update_data(self, data):
        for view_type, view in self.views.items():
            if self.config.visualizer.vis_view == view_type:
                view.update_data(data[view_type])
        self.canvas.update()

    def _update_lines_location(self, args=None):
        for view_type, view in self.views.items():
            if self.config.visualizer.vis_view == view_type:
                view.update_lines_location()
        self.camera.set_range(x=(0, self.config_local.width), y=(0, self.config_local.height), margin=0)
        self.canvas.update()


    def on_mouse_wheel(self, event):
        if vispy.util.keys.Key('Shift') in event.modifiers:
            if event.delta[1] > 0:
                self.config_local.line_space = int(self.config_local.line_space * self.config_local.line_space_coef)
            else:
                self.config_local.line_space = int(self.config_local.line_space / self.config_local.line_space_coef)
            self._update_plot_params()
            self._update_lines_location()
        else:
            if event.delta[1] > 0:
                self.config_local.line_scale *= self.config_local.line_scale_coef
            else:
                self.config_local.line_scale /= self.config_local.line_scale_coef
            print('line scale ts = ', self.config_local.line_scale)
            self._update_plot_params()
            self._update_lines_location()




class View:
    def __init__(self, config, config_local, canvas, vis_view, camera, line_color):
        self.config = config
        self.config_local = config_local
        self.vis_view = vis_view
        self.view = canvas.central_widget.add_view()
        self.view.visible = False
        self.view.camera = camera

        self.courser = 0
        self.points = None
        self.lines = Lines(self.config, self.config_local, self.view, self.vis_view, line_color)


    def update_lines_location(self):
        self.lines._update_lines_location()

    def update_lines_visibility(self):
        self.lines._update_lines_visibility()

    def draw_lines(self, color):
        self.lines.clear()
        self.lines = Lines(self.config, self.config_local, self.view, self.vis_view, color)

    def disable(self):
        self.view.visible = False

    def enable(self):
        self.view.visible = True

    def update_data(self, data):
        self.lines._update_data(data)


class Lines:
    n_points = None
    _update_data = None

    def __init__(self, config, config_local, view, vis_view, color):
        self.config = config
        self.config_local = config_local

        if vis_view in ['ECoG', 'hgECoG', 'hgA']:
            self.n_points = self.config.visualizer.n_samples_timeseries
            self._update_data = self._update_data_timeseries
        elif vis_view in ['Spec']:
            self.n_points = (self.config.visualizer.spec_ecog_high - self.config.visualizer.spec_ecog_low) * 2
            self._update_data = self._update_data_spectrum
        elif vis_view in ['hgSpec']:
            self.n_points = (self.config.visualizer.spec_hg_ecog_high - self.config.visualizer.spec_hg_ecog_low) * 2
            self._update_data = self._update_data_spectrum

        self.points = np.zeros((self.config.processor.n_channels, self.n_points, 2))
        self.points[:, :, 0] = np.linspace(0, 1, self.n_points).reshape((1, -1))

        self.lines = []
        for i in range(self.config.processor.n_channels):
            line = scene.Line(self.points[i, :, :], parent=view.scene, color=color)
            line.transform = scene.STTransform(translate=(0, self.config_local.offsets[i]),
                                               scale=(self.config_local.width, self.config_local.line_scale))
            line._visible = not self.config.processor.channels_bad[i]
            self.lines.append((line, i))
            view.add(line)
        self.courser = 0

    def clear(self):
        for line, i in self.lines:
            line.parent = None

    def _update_lines_location(self):
        for line, i in self.lines:
            line.transform = scene.STTransform(translate=(0, self.config_local.offsets[i]), scale=(self.config_local.width, self.config_local.line_scale))

    def _update_lines_visibility(self):
        for line, i in self.lines:
            line._visible = not self.config.processor.channels_bad[i]

    def _update_data_timeseries(self, data):
        if self.courser + data.shape[-1] < self.n_points:
            courser_new = self.courser + data.shape[-1]
            self.points[:,self.courser:courser_new, 1] = data
            self.courser = courser_new
        elif data.shape[-1] > self.n_points:
            self.points[:, :, 1] = data[:,-self.n_points:]
            self.courser = 0
        elif self.courser + data.shape[-1] > self.n_points:
            courser_new = self.courser + data.shape[-1] - self.n_points
            data_part1 = data[:,self.n_points - self.courser]
            data_part2 = data[:,self.n_points - self.courser:]
            self.points[:,self.courser:, 1] = data_part1
            self.points[:,courser_new, 1] = data_part2
        elif self.courser + data.shape[-1] == self.n_points:
            self.points[:, self.courser:, 1] = data
            self.courser = 0

        for line, i in self.lines:
            line.set_data(self.points[i, :, :])

    def _update_data_spectrum(self, data):
        assert data.shape[-1] == self.n_points, 'first dimension of the data and points should be the same'
        self.points[:, :, 1] = data

        for line, i in self.lines:
            line.set_data(self.points[i, :, :])





if __name__ == '__main__':
    pass
