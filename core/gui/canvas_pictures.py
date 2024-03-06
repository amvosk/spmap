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




class PicturesCanvas:

    def __init__(self, em, config):
        # Create a canvas and viewbox
        self.em = em
        self.config = config
        self.index = 0

        self.canvas = scene.SceneCanvas(keys='interactive')
        self.view = self.canvas.central_widget.add_view()

        self.text = scene.visuals.Text(str(self.index), parent=self.view.scene, color='black')
        self.text.transform = scene.STTransform(translate=(60, 40))

        self.image = scene.visuals.Image(
            vispy.io.image.imread(
                self.config.paths.resource_path/'assets/transitions/default.jpg') ,parent=self.view.scene, method='auto')

        rect = Rect(0, 0, *self.image.size)
        self.view.camera = scene.PanZoomCamera(rect=rect, aspect=1)
        self.view.camera.flip = (0,1,0)
        self.view.update()
        self.canvas.update()

        self.em.register_handler('experiment.transition', self.show_transition_picture)
        self.em.register_handler('experiment.present_collection_picture', self.show_collection_picture)

    def show_transition_picture(self, data):
        image_path = 'assets/transitions/{}.jpg'.format(data)
        self.update_image(image_path)

    def show_collection_picture(self, data):
        image_path = data
        self.update_image(image_path)
        
    def update_image(self, image_path):
        self.image.set_data(vispy.io.image.imread(self.config.paths.resource_path/image_path))
        self.view.camera.rect = Rect(0, 0, *self.image.size)
        self.view.update()
        self.canvas.update()


if __name__ == '__main__':
    pass
