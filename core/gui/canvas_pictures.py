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
        print(*self.image.size)

        rect = Rect(0, 0, *self.image.size)
        self.view.camera = scene.PanZoomCamera(rect=rect, aspect=1)
        self.view.camera.flip = (0,1,0)
        self.view.update()
        self.canvas.update()
        
    def update_image(self, value):
        try:
            if(value == 'pause'):
                img = 'assets/transitions/pause.jpg'
            elif(value == 'blink'):
                img = 'assets/transitions/blink.jpg'
            elif(value == 'finish'):
                img = 'assets/transitions/finish.jpg'
            elif(value == 'start'):
                img = 'assets/transitions/start.jpg'
            else:
                img = value.image_name

            # print(img)
            self.image.set_data(vispy.io.image.imread(self.config.paths.resource_path/img))
            self.text.text = str(value)
    
            self.view.camera.rect = Rect(0, 0, *self.image.size)
            self.view.update()
            self.canvas.update()
        except Empty:
            pass


if __name__ == '__main__':
    pass
