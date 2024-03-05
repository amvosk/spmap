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
    # line_scale = 1
    # line_space = 30

    def __init__(self, em, config):
        # Create a canvas and viewbox
        self.em = em
        self.config = config
        self.index = 0

        self.canvas = scene.SceneCanvas(keys='interactive')
        self.view = self.canvas.central_widget.add_view()

        # self.label = QtWidgets.QLabel()


        # self.image = scene.Image(parent=self.view.scene)
        resource_path = self.config.paths.resource_path
        self.resource_path = str(self.config.paths.resource_path) + '/'
        

        # self.images_preloaded = [vispy.io.image.imread('{}/{}.jpg'.format(images_path, name)) for name in images_name]
        ## path_pictures_objects_dir = resource_path  # / 'pictures_objects/'
        #print(path_pictures_objects_dir)

        ## path_pictures_objects_files = [
        ##    f for f in os.listdir(path_pictures_objects_dir) if os.path.isfile(os.path.join(path_pictures_objects_dir, f))
        ## ]
        ##path_pictures_objects_files.sort(key=lambda x: int(x[:-4]))
        ##self.images_preloaded = [vispy.io.image.imread(path_pictures_objects_dir / file) for file in path_pictures_objects_files]
        ##self.image = scene.visuals.Image(self.images_preloaded[self.index], parent=self.view.scene, method='auto')
        self.text = scene.visuals.Text(str(self.index), parent=self.view.scene, color='black')
        self.text.transform = scene.STTransform(translate=(60, 40))

        ##rect = Rect(0, 0, *self.image.size)
        ##self.view.camera = scene.PanZoomCamera(rect=rect, aspect=1)
        ##self.view.camera.flip = (0,1,0)
        ##self.view.update()
        ##self.canvas.update()
        self.image = scene.visuals.Image(vispy.io.image.imread(self.resource_path + 'assets/transitions/default.jpg') ,parent=self.view.scene, method='auto')
        rect = Rect(0, 0, *self.image.size)
        print(*self.image.size)
        self.view.camera = scene.PanZoomCamera(rect=rect, aspect=1)
        self.view.camera.flip = (0,1,0)
        self.view.update()
        self.canvas.update()
        
    def update_image(self, value):
        try:
            # value = queue
            
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
          
            self.image.set_data(vispy.io.image.imread(self.resource_path + img) )
            #print(*self.image.size)
 
            ##self.image.set_data(self.images_preloaded[value-1])
            ##self.image.set_data(vispy.io.image.imread(resource_path + value))
            self.text.text = str(value)
    
            self.view.camera.rect = Rect(0, 0, *self.image.size)
            self.view.update()
            self.canvas.update()
        except Empty:
            pass





        # self.images_preloaded = [np.asarray(Image.open('{}/{}.jpg'.format(images_path, name))) for name in images_name]
        # print([i.shape for i in self.images_preloaded])
        # self.images_preloaded = [QtGui.QPixmap('{}/{}.jpg'.format(images_path, name)) for name in images_name]
        # self.image.image = self.images_preloaded[0]
        # self.label.setPixmap(self.images_preloaded[0])
        # self.canvas.update()

        # self.em.register_handler('update config.receiver.channels', self._update_parametes)
        # self.em.register_handler('update config.recorder.channels_bad', self._channels_set_visible)
        # self.canvas.events.mouse_wheel.connect(self.on_mouse_wheel)
    #
    # def _update_parametes(self, config_receiver):
    #     self.config.receiver = copy.deepcopy(config_receiver)
    #     self.n_samples = self.config.receiver.fs * 3
    #     self.courser = 0
    #     self.n_lines = self.config.receiver.n_channels
    #     self.channels = self.config.receiver.channels
    #     self.points = np.zeros((self.n_samples, self.n_lines, 2))
    #     self.points[:, :, 0] = np.linspace(0, 1, self.n_samples).reshape((-1, 1))
    #     self._create_lines()
    #
    # def _create_lines(self):
    #     offsets, self.height = self._get_line_offsets()
    #     self.view.camera.set_range(x=(0, self.width), y=(0, self.height), margin=0)
    #
    #     for line in self.lines:
    #         if line is not None:
    #             line.parent = None
    #     self.lines = []
    #     line_counter = 0
    #     for i, state in enumerate(self.channels):
    #         if state:
    #             line = scene.Line(self.points[:, line_counter, :], parent=self.view.scene, color='blue')
    #             line.transform = scene.STTransform(translate=(0, offsets[line_counter]), scale=(self.width, self.line_scale))
    #             line._visible = not self.config.recorder.channels_bad[i]
    #             self.lines.append(line)
    #             self.view.add(line)
    #             line_counter += 1
    #         else:
    #             self.lines.append(None)
    #     self.canvas.update()
    #     self.em.trigger('update_brain_checkbox_height', copy.copy(self.height))
    #
    # def _update_line_offset(self):
    #     offsets, self.height = self._get_line_offsets()
    #     self.view.camera.set_range(x=(0, self.width), y=(0, self.height), margin=0)
    #     for i, line in enumerate(self.lines):
    #         if line is not None:
    #             line.transform = scene.STTransform(translate=(0, offsets[i]), scale=(self.width, self.line_scale))
    #     self.canvas.update()
    #     self.em.trigger('update_brain_checkbox_height', copy.copy(self.height))
    #
    #
    # def _get_line_offsets(self):
    #     height = (self.n_lines + 1) * self.line_space
    #     offsets = self.line_space * (np.arange(self.n_lines) + 1)
    #     offsets = offsets[::-1]
    #     return offsets, height
    #
    # def update_image(self, data):
    #     # print(data[:,0])
    #     if self.courser + data.shape[0] < self.n_samples:
    #         courser_new = self.courser + data.shape[0]
    #         self.points[self.courser:courser_new,:,1] = data
    #         self.courser = courser_new
    #     elif self.courser + data.shape[0] > self.n_samples:
    #         courser_new = self.courser + data.shape[0] - self.n_samples
    #         data_part1 = data[:self.n_samples - self.courser]
    #         data_part2 = data[self.n_samples - self.courser:]
    #         self.points[self.courser:, :, 1] = data_part1
    #         self.points[:courser_new, :, 1] = data_part2
    #     elif self.courser + data.shape[0] == self.n_samples:
    #         self.points[self.courser:, :, 1] = data
    #         self.courser = 0
    #
    #     for i, line in enumerate(self.lines):
    #         if line is not None:
    #             line.set_data(self.points[:,i,:])
    #     self.canvas.update()



    # def on_mouse_wheel(self, event):
    #     if vispy.util.keys.Key('Shift') in event.modifiers:
    #         if event.delta[1] > 0:
    #             self.line_space = int(self.line_space*1.5)
    #         else:
    #             self.line_space = int(self.line_space/1.5)
    #         self._update_line_offset()
    #     else:
    #         if event.delta[1] > 0:
    #             self.line_scale *= 1.2
    #         else:
    #             self.line_scale /= 1.2
    #         print(self.line_scale)
    #         for line in self.lines:
    #             if line is not None:
    #                 line.transform.scale = (self.width, self.line_scale)
    #         self.canvas.update()

# def callback_function(config, queue, canvas):
#     while True:
#         if not queue.empty():
#             chunk = queue.get()
#             data = chunk[:, :config.receiver.n_channels_max]
#             canvas.update_data(data)

if __name__ == '__main__':
    pass
