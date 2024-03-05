import numpy as np
from vispy import app, scene
from vispy.geometry import Rect
from functools import partial

class TimeSeriesCanvas:
    def __init__(self, lines_count=1):
        # Create a canvas and viewbox
        self.canvas_width, self.canvas_height = 800, 600
        self.view_sound_width, self.view_sound_height = self.canvas_width, 300
        self.view_ecog_width, self.view_ecog_height = self.canvas_width, self.canvas_height - self.view_sound_height
        self.n_samples = 200


        self.canvas = scene.SceneCanvas(keys='interactive', size=(self.canvas_width, self.canvas_height))
        self.view_ecog = self.canvas.central_widget.add_view()
        self.view_sound = self.canvas.central_widget.add_view()
        # self.view.camera = 'panzoom'
        # self.view.camera.set_range(x=[0, 500], y=[-5, 5])
        # self.view.camera.interactive=False

        rect_ecog = Rect(0, 0, self.view_ecog_width, self.view_ecog_height)
        rect_sound = Rect(0, 0, self.view_sound_width, self.view_sound_height)
        # self.view.camera = 'panzoom'
        # self.view.camera.set_range(x=[0, self.canvas_width], y=[0, self.canvas_hight])
        self.view_ecog.camera = scene.PanZoomCamera(rect=rect_ecog, interactive=False)
        self.view_sound.camera = scene.PanZoomCamera(rect=rect_sound, interactive=False)
        # self.view.camera.pan_button = None
        # self.view.camera.rect = self.canvas.size

        # Create a line plot for each time-series
        line_offsets = self._get_line_offsets(self.view_ecog_height, lines_count)
        self.line_scale = 1
        self.lines = []
        for i in range(lines_count):
            data = np.zeros((self.n_samples, 2))
            data[:, 0] = np.linspace(0, 1, self.n_samples)
            line = scene.Line(data, parent=self.view_ecog.scene, color='blue')
            line.transform = scene.STTransform(translate=(0,line_offsets[i]), scale=(self.canvas_width,self.line_scale))
            # line.transform.translate((0, 2))
            self.lines.append(line)

            # data[:, 0] = np.linspace(-1, 1, self.n_samples)
            # line = scene.Line(data, parent=self.view.scene, color='blue', edge_width=2)
            # line.transform = scene.STTransform(scale=(self.canvas_width / 2, 1))

            # Add the line plots to the viewbox
            self.view_ecog.add(line)
        self.canvas.events.mouse_wheel.connect(self.on_mouse_wheel)

    def _get_line_offsets(self, height, lines_count):
        line_offsets = height / (lines_count+1) * (np.arange(lines_count) + 1)
        return line_offsets


    def update_data(self, parent):
        for line in self.lines:
            data = np.zeros((self.n_samples, 2))
            data[:, 0] = np.linspace(0, 1, self.n_samples)
            data[:, 1] = np.random.normal(size=self.n_samples)
            line.set_data(data)
        self.canvas.update()
        print(self.line_scale)

    def show(self):
        self.canvas.show()

    def run(self):
        timer = app.Timer(interval=0.1, connect=self.update_data, start=True)
        app.run()

    def on_mouse_wheel(self, event):
        if event.delta[1] > 0:
            self.line_scale *= 1.1
        else:
            self.line_scale /= 1.1
        for line in self.lines:
            line.transform.scale = (self.canvas_width,self.line_scale)
        self.canvas.update()



canvas = TimeSeriesCanvas(lines_count=10)
canvas.show()
canvas.run()



# view.camera = 'panzoom'
# view.camera.set_range(x=[0, 500], y=[-5, 5])
# # view.camera.rect = canvas.size
# # Create a line plot of the EEG data
# colors = ['red', 'blue', 'green']
# lines = [scene.Line(np.random.normal(size=(100, 2)), parent=view.scene, color=color) for color in colors]
#
# # Add the line plot to the viewbox
# for line in lines:
#     view.add(line)
#
# # Define an update function that will be called to update the data
# def update_data(self):
#     data = np.zeros((100, 2))
#     data[:, 0] = np.linspace(0, 500, 100)
#     for line in lines:
#         data[:, 1] = np.random.normal(size=(100))
#         line.set_data(np.copy(data))
#     canvas.update()
#
#
# # Start the app and schedule the update function to be called periodically
# timer = app.Timer(interval=0.1, connect=update_data, start=True)
# canvas.show()
# app.run()