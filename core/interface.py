import copy
import sys
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtWidgets import QDialog,  QToolBar, QSizePolicy
from PyQt6.QtGui import QAction, QIcon

from vispy import scene
from functools import partial
from gui.canvas_timeseries import TimeSeriesCanvas
from gui.canvas_sound import SoundCanvas
from gui.canvas_pictures import PicturesCanvas
from gui.canvas_results_summary import ResultsSummaryCanvasWrapper
# from config import LocalConfig

sys.path.insert(0, '../generation/')
from generator import GeneratorLSL
from record_lsl import RecordLSL
from receiver import Receiver
from recorder import Recorder
from processor import Processor
from experiment import Experiment
from stimulus import Stimulus

from vispy.app import use_app
use_app('pyqt6')

class MainWindow(QtWidgets.QMainWindow):
    stimulus = None
    processor = None
    generator_lsl = None
    receiver = None

    def __init__(self, config, em):
        super().__init__()
        self.config = config
        self.em = em
        # self.config_local = LocalConfig(self.config, self.em)

        # self.amplifiers = [self.config.receiver.lsl_stream_name_debug]
        self.receiver = Receiver(self.config, self.em)
        self.recorder = Recorder(self.config, self.em)
        self.processor = Processor(self.config, self.em, self)
        self.experiment = Experiment(self.config, self.em, self)
        self.stimulus = Stimulus(self.config, self.em)
        self.generator_lsl = GeneratorLSL(self.config, self.em)
        self.record_lsl = RecordLSL(self.config, self.em)
        self.record_lsl.queue = self.experiment.queue

        self.timer_connect = QtCore.QTimer(self) 
        self.timer_experiment = None
        self.setWindowTitle("Passive Speech Mapping")
        # Create the canvases

        self.create_menu_bar()

        self.control_widget = self.create_control_widget()
        self.timeseries = TimeSeriesCanvas(self.em, self.config)
        self.canvas_pictures = PicturesCanvas(self.em, self.config)
        self.sound = SoundCanvas(self.em, self.config)
        self.canvas_results_summary = ResultsSummaryCanvasWrapper(self.em, self.config)
        self.canvas_results_decoder = ResultsSummaryCanvasWrapper(self.em, self.config)
        # self.canvas_results_decoder = scene.SceneCanvas(keys='interactive')
        # self.view_results_raster = self.canvas_results_decoder.central_widget.add_view()

        layout_brain = QtWidgets.QHBoxLayout()
        layout_brain.setContentsMargins(0,0,0,0) ### Clean?
        widget_brain = QtWidgets.QWidget()
        widget_brain.setLayout(layout_brain)
        #widget_brain.setStyleSheet("background-color: white")
        #widget_brain.setStyleSheet("QWidget { border: 1px solid gray;} QCheckBox{border: none;}") ##clean?

        self.layout_brain_checkbox = QtWidgets.QVBoxLayout()
        self.widget_brain_checkbox = QtWidgets.QWidget()
        self.widget_brain_checkbox.setLayout(self.layout_brain_checkbox)
        self.widget_brain_checkbox.setFixedWidth(60)
        self.brain_checkbox = []
        self.create_brain_checkbox()
        self.em.register_handler('update config.processor.channels', self.create_brain_checkbox)

        widget_splitter_timeseries = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        splitter_checkboxes_ecog = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter_checkboxes_ecog.addWidget(self.widget_brain_checkbox)
        splitter_checkboxes_ecog.addWidget(self.timeseries.canvas.native)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(splitter_checkboxes_ecog)
        scroll_area.setWidgetResizable(True)
        layout_brain.addWidget(scroll_area)

        widget_splitter_timeseries.addWidget(widget_brain)
        widget_splitter_timeseries.addWidget(self.sound.canvas.native)
        size_brain = int(widget_splitter_timeseries.size().width() * 0.8)
        size_sound = widget_splitter_timeseries.size().width() - size_brain
        widget_splitter_timeseries.setSizes([size_brain, size_sound])

        widget_splitter_images = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        widget_results = QtWidgets.QTabWidget()
        widget_results.addTab(self.canvas_results_summary.canvas.native, "Summary")
        widget_results.addTab(self.canvas_results_decoder.canvas.native, "Decoder")
        widget_splitter_images.addWidget(self.canvas_pictures.canvas.native)
        widget_splitter_images.addWidget(widget_results)
        part_pictures = int(widget_splitter_images.size().height() * 0.4)
        part_results = widget_splitter_images.size().height() - part_pictures
        widget_splitter_images.setSizes([part_pictures, part_results])

        widget_splitter_canvases = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        widget_splitter_canvases.addWidget(widget_splitter_timeseries)
        widget_splitter_canvases.addWidget(widget_splitter_images)
        size_timeseries = int(widget_splitter_canvases.size().width() * 0.79)
        size_results = widget_splitter_canvases.size().width() - size_timeseries
        widget_splitter_canvases.setSizes([size_timeseries, size_results])

        # Создаем заголовок (header)

        header_layout = QtWidgets.QHBoxLayout()

        # Добавляем логотип
        logo_label = QtWidgets.QLabel()
        logo_icon = QIcon(str(self.config.paths.resource_path) + "/icons/spmap.svg").pixmap(40, 40)
        logo_label.setPixmap(logo_icon)

        # Создаем QLabel для текста "Server"
        title_label = QtWidgets.QLabel("ELoQ")
        title_font = QtGui.QFont("Runic", 16)  # Настраиваем шрифт
        title_font.setBold(False)

        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        header_layout.setSpacing(10)
        header_layout.setContentsMargins(10,10,10,10)
        header = QtWidgets.QWidget()
        header.setLayout(header_layout)
        header.setStyleSheet("background-color:black")

        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        header.setSizePolicy(sizePolicy)

        # header.setVerticalPolicy(0)#QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        # Добавляем вертикальный отступ между логотипом и заголовком
        #header_layout.addItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        # Создаем вертикальный макет для body
        body_layout = QtWidgets.QVBoxLayout()
        # for k, v in vars(QtWidgets.QSizePolicy).items():
        #     print(k, v)
        body = QtWidgets.QWidget()
        body.setLayout(body_layout)
        # Добавляем макет заголовка в body_layout
        #body_layout.addLayout(header_layout)

        # Создаем горизонтальный макет для основной части
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(0,5,5,0)
        # Добавляем виджеты в main_layout
        main_layout.addWidget(self.control_widget)  
        main_layout.addWidget(widget_splitter_canvases)
        main = QtWidgets.QWidget()
        main.setLayout(main_layout)
        # Добавляем main_layout в body_layout
        #body_layout.addLayout(main_layout)
        body_layout.addWidget(header)
        body_layout.addWidget(main)
        body_layout.setContentsMargins(0,0,0,0)
        # Устанавливаем центральный виджет для главного окна
        self.setCentralWidget(body)

        self.showMaximized()

    def closeEvent(self, event):
        # Call your function here
        if self.receiver is not None:
            self.receiver.terminate()
        if self.generator_lsl is not None:
            self.generator_lsl.stop()
        if self.record_lsl is not None:
            self.record_lsl.stop()
        # Accept the close event to close the window
        event.accept()

    def create_brain_checkbox(self, args=None):
        while self.layout_brain_checkbox.count():
            child = self.layout_brain_checkbox.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.brain_checkbox = []
        # for index, state in enumerate(self.config.processor.channels):
        for i in range(self.config.processor.n_channels):
            checkbox = QtWidgets.QCheckBox("{}".format(i + 1))
            checkbox.setChecked(True)
            checkbox.setStyleSheet(
                "QCheckBox::indicator {"
                "    border: 1px solid black; background-color: black"
                "}"
                "QCheckBox::indicator:checked {"
                "    background-color: white; color: black"
                "}"
            )
            checkbox.stateChanged.connect(
                lambda state, index=i: self.handle_stateChanged_brain_checkbox(state, index)
            )
            self.brain_checkbox.append(checkbox)
            self.layout_brain_checkbox.addWidget(checkbox)


    def handle_stateChanged_brain_checkbox(self, state, index):
        self.em.trigger('update config.processor.channels_bad', (index, state))

    def create_menu_bar(self):

        menu_bar = self.menuBar()

        style_sheet = """
            QMenuBar {
                background-color: #D9D9D9;
                border: 1px solid #D9D9D9;
                height: 54px;
            }
        """

        icon_path = "../resource/icons/brain.svg"
        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(QtGui.QPixmap(icon_path))

        # Create the "File" menu
        file_menu = menu_bar.addMenu("File")

        # Создаем меню Help
        help_menu = menu_bar.addMenu("Help")

        # Создаем действие (Action) для меню Help
        help_action = QAction("Help", self)

        # Применяем стили к тексту в действии
        style_sheet_action = """
            QAction {
                color: #000;
                font-family: Saira;
                font-size: 16px;
                font-style: normal;
                font-weight: 600;
                line-height: normal;
            }
        """
        help_menu.setStyleSheet(style_sheet_action)

        # Добавляем действие в меню
        help_menu.addAction(help_action)

        file_menu.addAction("Open")
        file_menu.addAction("Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        help_menu.addAction("About")

        config_menu = menu_bar.addMenu("Configuration")
        config_menu.addAction("Dark Theme", lambda: self.change_theme('dark'))
        config_menu.addAction("Light Theme", lambda: self.change_theme('light'))



    # def create_menu_bar(self):
    #     menu_bar = self.menuBar()
    #     style_sheet = """
    #         QMenuBar {
    #             background-color: #D9D9D9;
    #             border: 1px solid #D9D9D9;
    #             height: 54px;
    #         }
    #     """
    #     toolbar = QToolBar("My main toolbar")
    #     toolbar.setIconSize(QtCore.QSize(56, 56))
    #     self.addToolBar(toolbar)
    #
    #     button_action = QAction(QIcon(str(self.config.paths.resource_path) + "/icons/brain.svg"), "&Your button", self)
    #     button_action.setStatusTip("This is your button")
    #     #button_action.triggered.connect(self.onMyToolBarButtonClick)
    #     button_action.setCheckable(True)
    #     toolbar.addAction(button_action)
    #     toolbar.addSeparator()
    #
    #     menu_bar.setStyleSheet(style_sheet)
    #     # Create the "File" menu
    #     file_menu = menu_bar.addMenu("File")
    #
    #     # Создаем меню Help
    #     help_menu = menu_bar.addMenu("Help")
    #
    #     # Создаем действие (Action) для меню Help
    #     help_action = QAction("Help", self)
    #
    #     # Применяем стили к тексту в действии
    #     style_sheet_action = """
    #         QAction {
    #             color: #000;
    #             font-family: Saira;
    #             font-size: 16px;
    #             font-style: normal;
    #             font-weight: 600;
    #             line-height: normal;
    #         }
    #     """
    #     help_menu.setStyleSheet(style_sheet_action)
    #
    #     # Добавляем действие в меню
    #     help_menu.addAction(help_action)
    #
    #     file_menu.addAction("Open")
    #     file_menu.addAction("Save")
    #     file_menu.addSeparator()
    #     file_menu.addAction("Exit", self.close)
    #     help_menu.addAction("About")
    #
    #     config_menu = menu_bar.addMenu("Configuration")
    #     config_menu.addAction("Patient")
    #     config_menu.addAction("Experiment")
    #     config_menu.addAction("Receiver", self.receiver_dialog)
    #     config_menu.addAction("Vizualization")
    #
    # def create_menu_bar(self):
    #
    #     menu_bar = self.menuBar()
    #
    #     style_sheet = """
    #         QMenuBar {
    #             background-color: #D9D9D9;
    #             border: 1px solid #D9D9D9;
    #             height: 54px;
    #         }
    #     """
    #
    #     icon_path = "../resource/icons/brain.svg"
    #     icon_label = QtWidgets.QLabel()
    #     icon_label.setPixmap(QtGui.QPixmap(icon_path))
    #
    #     menu_bar.setStyleSheet(style_sheet)
    #     # Create the "File" menu
    #     file_menu = menu_bar.addMenu("File")
    #
    #     # Создаем меню Help
    #     help_menu = menu_bar.addMenu("Help")
    #
    #     # Создаем действие (Action) для меню Help
    #     help_action = QAction("Help", self)
    #
    #     # Применяем стили к тексту в действии
    #     style_sheet_action = """
    #         QAction {
    #             color: #000;
    #             font-family: Saira;
    #             font-size: 16px;
    #             font-style: normal;
    #             font-weight: 600;
    #             line-height: normal;
    #         }
    #     """
    #     help_menu.setStyleSheet(style_sheet_action)
    #
    #     # Добавляем действие в меню
    #     help_menu.addAction(help_action)
    #
    #     file_menu.addAction("Open")
    #     file_menu.addAction("Save")
    #     file_menu.addSeparator()
    #     file_menu.addAction("Exit", self.close)
    #     help_menu.addAction("About")
    #
    #     config_menu = menu_bar.addMenu("Configuration")
    #     config_menu.addAction("Dark Theme", lambda: self.change_theme('dark'))
    #     config_menu.addAction("Light Theme", lambda: self.change_theme('light'))

    def change_theme(self, theme):
        if theme == 'dark':
            self.timeseries.canvas.bgcolor = (0, 0, 0, 1)
            self.timeseries.line_color = 'white'
            self.timeseries._draw_channels()
            #self.sound.canvas.bgcolor = (0, 0, 0, 1)
        elif theme == 'light':
            self.timeseries.canvas.bgcolor = (1, 1, 1, 1)
            self.timeseries.line_color = 'black'
            self.timeseries._draw_channels()

            #self.sound.canvas.bgcolor = (1, 1, 1, 1)

   

    def create_control_widget(self):
        control_layout = QtWidgets.QVBoxLayout()
        control_layout.setSpacing(30)
        control_layout.setContentsMargins(7, 20, 0, 0)
        control_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)

        # icons_path = "../resource/icons/"
        icons_style = """
            QPushButton {
                border: none;
                background-color: none;
            }
            QPushButton:hover {
                background-color: white;
                border-radius: 6px;
                border: 2px solid gray
            }
            QPushButton:pressed {
                background-color: white;
                border-radius: 6px;
                border: 2px solid gray
            }
            QWidget {
                }
        """
        #Можно переделать в экземпляры класса Icon(QtWidgets.QPushButton, name): self.path = resource_path + name
        start_icon = QtWidgets.QPushButton()
        start_icon.setIcon(QIcon(str(self.config.paths.resource_path) + "/icons/start.svg"))
        start_icon.setIconSize(QtCore.QSize(30, 30))    
        start_icon.clicked.connect(lambda: icon_clicked(start_icon))
        #start_icon.setStyleSheet("border-top: 1px solid black;border-bottom: 1px solid black; background-color: none;")
        start_icon.setFixedSize(QtCore.QSize(40,40))

        receiver_icon = QtWidgets.QPushButton()
        receiver_icon.setIcon(QIcon(str(self.config.paths.resource_path) + "/icons/receiver.svg"))
        receiver_icon.setIconSize(QtCore.QSize(30, 30))    
        receiver_icon.clicked.connect(lambda: icon_clicked(receiver_icon))
        receiver_icon.setFixedSize(QtCore.QSize(40,40))

        settings_icon = QtWidgets.QPushButton()
        settings_icon.setIcon(QIcon(str(self.config.paths.resource_path) + "/icons/settings.svg"))
        settings_icon.setIconSize(QtCore.QSize(30, 30))    
        settings_icon.clicked.connect(lambda: icon_clicked(settings_icon))
        settings_icon.setFixedSize(QtCore.QSize(40,40))

        patient_icon = QtWidgets.QPushButton()
        patient_icon.setIcon(QIcon(str(self.config.paths.resource_path) + "/icons/user.svg"))
        patient_icon.setIconSize(QtCore.QSize(30, 30))    
        patient_icon.clicked.connect(lambda: icon_clicked(patient_icon))
        patient_icon.setFixedSize(QtCore.QSize(40,40))

        eloq_icon = QtWidgets.QPushButton()
        eloq_icon.setIcon(QIcon(str(self.config.paths.resource_path) + "/icons/eloq.svg"))
        eloq_icon.setIconSize(QtCore.QSize(30, 30))    
        eloq_icon.clicked.connect(lambda: icon_clicked(eloq_icon))
      
        eloq_icon.setFixedSize(QtCore.QSize(40,40))
        
        def get_start_icon():
            return start_icon


        def icon_clicked(icon_path): #передавать сюда сам объект виджета кнопки чтобы менять его стиль при нажатии
            active_icon ="background-color: gray; border: none; opacity: 0.1; border-radius: 6px;"
            if icon_path == start_icon:
                pass
                #icon_path.setIcon(QIcon(icons_path + "pause.svg"))
                ## self.start()
            elif icon_path == receiver_icon:
                self.receiver_dialog()
                #icon_path.setStyleSheet(active_icon)
                #icon_path.setIconSize(QtCore.QSize(40,40))
                #icon_path.setIcon(QIcon(icons_path + "receiver_active.svg"))
            elif icon_path == settings_icon:
                self.vizualizer_dialog()
                #icon_path.setIconSize(QtCore.QSize(40,40))
                #icon_path.setStyleSheet(active_icon)
                #self.receiver_dialog()
            elif icon_path == eloq_icon:
                self.experiment_dialog()
                #icon_path.setIconSize(QtCore.QSize(40,40))
                #icon_path.setStyleSheet(active_icon)
                #self.experiment_dialog()
            elif icon_path == patient_icon:
                #icon_path.setIconSize(QtCore.QSize(40,40))
                #icon_path.setStyleSheet(active_icon)
                self.patient_dialog()


        control_layout.addWidget(start_icon)
        control_layout.addWidget(receiver_icon)
        control_layout.addWidget(settings_icon)
        control_layout.addWidget(patient_icon)
        control_layout.addWidget(eloq_icon)

        control_widget = QtWidgets.QWidget()
        control_widget.get_start_icon = lambda: get_start_icon()
        control_widget.setLayout(control_layout)
        control_widget.setFixedWidth(50)
        control_widget.setContentsMargins(0,0,0,0)
        control_widget.setStyleSheet(icons_style)
        
        return control_widget


    def receiver_dialog(self):
        receiver_window = ReceiverWindow(
            self.config, self.em, self.receiver, self.generator_lsl, self.record_lsl, self.experiment,
            self.processor, self.timeseries, self.sound, self.timer_connect,self.control_widget)
        #receiver_window.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        receiver_window.exec()

    def vizualizer_dialog(self):
        vizualizer_window = VizualizerWindow(self.config, self.em)
        vizualizer_window.exec()


    def patient_dialog(self):
        patient_window = PatientWindow(self.config, self.em)
        patient_window.exec()
        
    def experiment_dialog(self):
        experiment_window = ExperimentWindow(self.config, self.em, self.experiment)
        experiment_window.exec()

    def run_all(self):
        pass


class VizualizerWindow(QtWidgets.QDialog):
    def __init__(self, config, em):
        super().__init__()
        self.config = config 
        self.em = em
        layout_visualization = QtWidgets.QVBoxLayout()
        widget_visualization = QtWidgets.QWidget()
        #widget_visualization.setLayout(layout_visualization)
        self.setLayout(layout_visualization)
        self.setWindowTitle("Advanced Settings")

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout_visualization.addWidget(separator)

        label_visualization = QtWidgets.QLabel("Visualization")
        label_visualization.setObjectName("visualization_label")
        layout_visualization.addWidget(label_visualization)

        button_visualization_parameters = QtWidgets.QPushButton("Parameters")
        button_visualization_parameters.setObjectName("button_experiment_parameters")
        button_visualization_parameters.clicked.connect(
            partial(self.handle_button_visualization_parameters_clicked, button_visualization_parameters, widget_visualization)
        )
        layout_visualization.addWidget(button_visualization_parameters)

        layout_visualization_settings = QtWidgets.QHBoxLayout()
        widget_visualization_settings = QtWidgets.QWidget()
        widget_visualization_settings.setLayout(layout_visualization_settings)
        layout_visualization.addWidget(widget_visualization_settings)

        layout_visualization_type = QtWidgets.QVBoxLayout()
        widget_visualization_type = QtWidgets.QWidget()
        widget_visualization_type.setLayout(layout_visualization_type)
        layout_visualization_settings.addWidget(widget_visualization_type)

        self.button_group_visualization_type = QtWidgets.QButtonGroup()
        visualization_types = ["ECoG", "Spec", "hgECoG", "hgSpec", "hgA"]
        for visualization_type in visualization_types:
            radio_button = QtWidgets.QRadioButton(visualization_type)
            radio_button.setObjectName(visualization_type)
            self.button_group_visualization_type.addButton(radio_button)
            layout_visualization_type.addWidget(radio_button)
        self.button_group_visualization_type.setExclusive(True)
        self.button_group_visualization_type.buttonClicked.connect(self.handle_button_visualization_type_buttonClicked)
        self.button_group_visualization_type.buttons()[0].setChecked(True)

        layout_visualization_parameters_checkbox = QtWidgets.QVBoxLayout()
        widget_visualization_parameters_checkbox = QtWidgets.QWidget()
        widget_visualization_parameters_checkbox.setLayout(layout_visualization_parameters_checkbox)
        layout_visualization_settings.addWidget(widget_visualization_parameters_checkbox)

        checkbox_notch_filter_naive_ecog = QtWidgets.QCheckBox("eNotch")
        checkbox_notch_filter_naive_ecog.setChecked(self.config.visualizer.ecog_notch)
        checkbox_notch_filter_naive_ecog.stateChanged.connect(
            self.handle_checkbox_notch_filter_naive_ecog_stateChanged)
        layout_visualization_parameters_checkbox.addWidget(checkbox_notch_filter_naive_ecog)

        checkbox_highpass_filter_naive_ecog = QtWidgets.QCheckBox("eHP")
        checkbox_highpass_filter_naive_ecog.setChecked(self.config.visualizer.ecog_highpass_filter)
        checkbox_highpass_filter_naive_ecog.stateChanged.connect(
            self.handle_checkbox_highpass_filter_naive_ecog_stateChanged)
        layout_visualization_parameters_checkbox.addWidget(checkbox_highpass_filter_naive_ecog)

        checkbox_lowpass_filter_naive_ecog = QtWidgets.QCheckBox("eLP")
        checkbox_lowpass_filter_naive_ecog.setChecked(self.config.visualizer.ecog_lowpass_filter)
        checkbox_lowpass_filter_naive_ecog.stateChanged.connect(
            self.handle_checkbox_lowpass_filter_naive_ecog_stateChanged)
        layout_visualization_parameters_checkbox.addWidget(checkbox_lowpass_filter_naive_ecog)

    def handle_button_visualization_parameters_clicked(self, button, widget):
        visualization_parameters_window = VisualizationParametersWindow(self.config, self.em)
        # visualization_parameters_window = ExperimentParametersWindow(self.config, self.em, self.stimulus)
        visualization_parameters_window.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        x = widget.geometry().x() + widget.geometry().width()
        y = widget.geometry().y() + 100
        visualization_parameters_window.move(x, y)
        visualization_parameters_window.setWindowFlags(
            visualization_parameters_window.windowFlags() | QtCore.Qt.WindowType.CustomizeWindowHint)
        visualization_parameters_window.setWindowFlags(
            visualization_parameters_window.windowFlags() & ~QtCore.Qt.WindowType.WindowCloseButtonHint)
        visualization_parameters_window.exec()
    
    def handle_button_visualization_type_buttonClicked(self):
        selected_button = self.button_group_visualization_type.checkedButton()
        self.em.trigger('update config.visualizer.vis_view', selected_button.text())
    
    def handle_checkbox_notch_filter_naive_ecog_stateChanged(self, state):
        self.em.trigger('update config.visualizer.ecog_notch', state)

    def handle_checkbox_highpass_filter_naive_ecog_stateChanged(self, state):
        self.em.trigger('update config.visualizer.ecog_highpass_filter', state)

    def handle_checkbox_lowpass_filter_naive_ecog_stateChanged(self, state):
        self.em.trigger('update config.visualizer.ecog_lowpass_filter', state)


class VisualizationParametersWindow(QtWidgets.QDialog):
    def __init__(self, config, em):
        super().__init__()
        self.config = config
        self.em = em
        self.config_visualization = copy.deepcopy(self.config.visualizer)
        self.config_visualization_copy = copy.deepcopy(self.config.visualizer)
        self.setWindowTitle("Visualization Parameters")

        layout_visualization_parameters_window = QtWidgets.QVBoxLayout()
        self.setLayout(layout_visualization_parameters_window)

        layout_visualization_parameters_values = QtWidgets.QFormLayout()
        # layout_visualization_parameters_values.setVerticalSpacing(10)
        widget_visualization_parameters_values = QtWidgets.QWidget()
        widget_visualization_parameters_values.setLayout(layout_visualization_parameters_values)
        layout_visualization_parameters_window.addWidget(widget_visualization_parameters_values)

        field_size = 80

        checkbox_amplitude_downsample = QtWidgets.QCheckBox()
        checkbox_amplitude_downsample.setChecked(self.config_visualization.downsample)
        layout_visualization_parameters_values.addRow("downsample", checkbox_amplitude_downsample)

        field_fs_downsample = QtWidgets.QLineEdit()
        field_fs_downsample.setFixedWidth(field_size)
        field_fs_downsample.setText(str(self.config_visualization.fs_downsample))
        layout_visualization_parameters_values.addRow("fs downsample", field_fs_downsample)

        field_n_samples_timeseries_sec = QtWidgets.QLineEdit()
        field_n_samples_timeseries_sec.setFixedWidth(field_size)
        field_n_samples_timeseries_sec.setText(str(self.config_visualization.n_samples_timeseries_sec))
        layout_visualization_parameters_values.addRow("vis seconds", field_n_samples_timeseries_sec)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout_visualization_parameters_values.addWidget(separator)

        field_notch_filter_naive_ecog_Q = QtWidgets.QLineEdit()
        field_notch_filter_naive_ecog_Q.setFixedWidth(field_size)
        field_notch_filter_naive_ecog_Q.setText(str(self.config_visualization.notch_q))
        layout_visualization_parameters_values.addRow("Notch Q", field_notch_filter_naive_ecog_Q)

        field_notch_filter_naive_ecog_N = QtWidgets.QLineEdit()
        field_notch_filter_naive_ecog_N.setFixedWidth(field_size)
        field_notch_filter_naive_ecog_N.setText(str(self.config_visualization.notch_n))
        layout_visualization_parameters_values.addRow("Notch N harmonics", field_notch_filter_naive_ecog_N)

        field_highpass_filter_naive_ecog = QtWidgets.QLineEdit()
        field_highpass_filter_naive_ecog.setFixedWidth(field_size)
        field_highpass_filter_naive_ecog.setText(str(self.config_visualization.ecog_hpf))
        layout_visualization_parameters_values.addRow("ECoG high-pass filter", field_highpass_filter_naive_ecog)

        field_lowpass_filter_naive_ecog = QtWidgets.QLineEdit()
        field_lowpass_filter_naive_ecog.setFixedWidth(field_size)
        field_lowpass_filter_naive_ecog.setText(str(self.config_visualization.ecog_lpf))
        layout_visualization_parameters_values.addRow("ECoG low-pass filter", field_lowpass_filter_naive_ecog)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout_visualization_parameters_values.addWidget(separator)

        layout_bandpass_filter_hg_ecog = QtWidgets.QHBoxLayout()
        field_bandpass_filter_hg_ecog_low = QtWidgets.QLineEdit()
        field_bandpass_filter_hg_ecog_low.setFixedWidth(field_size // 2 - 3)
        field_bandpass_filter_hg_ecog_low.setText(str(self.config_visualization.hg_ecog_bpfl))
        field_bandpass_filter_hg_ecog_high = QtWidgets.QLineEdit()
        field_bandpass_filter_hg_ecog_high.setFixedWidth(field_size // 2 - 3)
        field_bandpass_filter_hg_ecog_high.setText(str(self.config_visualization.hg_ecog_bpfh))
        layout_bandpass_filter_hg_ecog.addWidget(field_bandpass_filter_hg_ecog_low)
        layout_bandpass_filter_hg_ecog.addWidget(field_bandpass_filter_hg_ecog_high)
        layout_visualization_parameters_values.addRow("hgECoG band-pass filter", layout_bandpass_filter_hg_ecog)

        checkbox_amplitude_log_transform = QtWidgets.QCheckBox()
        checkbox_amplitude_log_transform.setChecked(self.config_visualization.log_transform)
        layout_visualization_parameters_values.addRow("log transform", checkbox_amplitude_log_transform)

        field_smoother_filter_gh_ecog = QtWidgets.QLineEdit()
        field_smoother_filter_gh_ecog.setFixedWidth(field_size)
        field_smoother_filter_gh_ecog.setText(str(self.config_visualization.hg_ecog_sf))
        layout_visualization_parameters_values.addRow("hgECoG smoother filter", field_smoother_filter_gh_ecog)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout_visualization_parameters_values.addWidget(separator)

        layout_spectrum_naive_ecog = QtWidgets.QHBoxLayout()
        field_spectrum_naive_ecog_low = QtWidgets.QLineEdit()
        field_spectrum_naive_ecog_low.setFixedWidth(field_size // 2 - 3)
        field_spectrum_naive_ecog_low.setText(str(self.config_visualization.spec_ecog_low))
        field_spectrum_naive_ecog_high = QtWidgets.QLineEdit()
        field_spectrum_naive_ecog_high.setFixedWidth(field_size // 2 - 3)
        field_spectrum_naive_ecog_high.setText(str(self.config_visualization.spec_ecog_high))
        layout_spectrum_naive_ecog.addWidget(field_spectrum_naive_ecog_low)
        layout_spectrum_naive_ecog.addWidget(field_spectrum_naive_ecog_high)
        layout_visualization_parameters_values.addRow("Spectrum freq ECoG", layout_spectrum_naive_ecog)

        layout_spectrum_hg_ecog = QtWidgets.QHBoxLayout()
        field_spectrum_hg_ecog_low = QtWidgets.QLineEdit()
        field_spectrum_hg_ecog_low.setFixedWidth(field_size // 2 - 3)
        field_spectrum_hg_ecog_low.setText(str(self.config_visualization.spec_hg_ecog_low))
        field_spectrum_hg_ecog_high = QtWidgets.QLineEdit()
        field_spectrum_hg_ecog_high.setFixedWidth(field_size // 2 - 3)
        field_spectrum_hg_ecog_high.setText(str(self.config_visualization.spec_hg_ecog_high))
        layout_spectrum_hg_ecog.addWidget(field_spectrum_hg_ecog_low)
        layout_spectrum_hg_ecog.addWidget(field_spectrum_hg_ecog_high)
        layout_visualization_parameters_values.addRow("Spectrum freq hgECoG", layout_spectrum_hg_ecog)

        field_spectrum_exp_decay = QtWidgets.QLineEdit()
        field_spectrum_exp_decay.setFixedWidth(field_size)
        field_spectrum_exp_decay.setText(str(self.config_visualization.spec_decay))
        layout_visualization_parameters_values.addRow("Spectrum decay", field_spectrum_exp_decay)

        field_spectrum_window_size = QtWidgets.QLineEdit()
        field_spectrum_window_size.setFixedWidth(field_size)
        field_spectrum_window_size.setText(str(self.config_visualization.spec_window_size))
        layout_visualization_parameters_values.addRow("Spectrum window, sec", field_spectrum_window_size)

        widget_out_buttons = self.create_widget_out_buttons()
        layout_visualization_parameters_window.addWidget(widget_out_buttons)


    # def handle_checkbox_amplitude_log_transform
    # self.em.register_handler('update config.visualizer.update_log_transform', self.update_log_transform)

    def create_widget_out_buttons(self):
        layout_out_buttons = QtWidgets.QHBoxLayout()
        widget_out_buttons = QtWidgets.QWidget()
        widget_out_buttons.setLayout(layout_out_buttons)

        button_visualization_parameters_save = QtWidgets.QPushButton("Save")
        button_visualization_parameters_save.clicked.connect(self.handle_clicked_button_visualization_parameters_save)
        layout_out_buttons.addWidget(button_visualization_parameters_save)

        button_visualization_parameters_cancel = QtWidgets.QPushButton("Cancel")
        button_visualization_parameters_cancel.clicked.connect(self.handle_clicked_button_visualization_parameters_cancel)
        layout_out_buttons.addWidget(button_visualization_parameters_cancel)

        button_visualization_parameters_reset = QtWidgets.QPushButton("Reset")
        button_visualization_parameters_reset.clicked.connect(self.handle_clicked_button_visualization_parameters_reset)
        layout_out_buttons.addWidget(button_visualization_parameters_reset)

        return widget_out_buttons


    def handle_clicked_button_visualization_parameters_save(self):
        for field_name, field_value in vars(self.config_visualization).items():
            self.em.trigger('update config.visualizer.{}'.format(field_name), field_value)
        self.em.trigger('update config.visualizer parameters')
        self.close()

    def handle_clicked_button_visualization_parameters_cancel(self):
        self.close()

    def handle_clicked_button_visualization_parameters_reset(self):
        self.config_visualization = copy.deepcopy(self.config_visualization_copy)




class ExperimentParametersWindow(QtWidgets.QDialog):
    def __init__(self, config, em, stimulus):
        super().__init__()
        self.config = config
        self.em = em
        self.stimulus = stimulus
        self.config_experiment = copy.deepcopy(self.config.experiment)
        self.config_experiment_copy = copy.deepcopy(self.config.experiment)
        self.setWindowTitle("Experiment Parameters")

        layout_experiment_parameters_window = QtWidgets.QVBoxLayout()
        self.setLayout(layout_experiment_parameters_window)

        layout_experiment_parameters = QtWidgets.QHBoxLayout()
        widget_experiment_parameters = QtWidgets.QWidget()
        widget_experiment_parameters.setLayout(layout_experiment_parameters)
        layout_experiment_parameters_window.addWidget(widget_experiment_parameters)

        layout_experiment_parameters_task = QtWidgets.QFormLayout()
        widget_experiment_parameters_task = QtWidgets.QWidget()
        widget_experiment_parameters_task.setLayout(layout_experiment_parameters_task)
        # layout_experiment_parameters_task.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout_experiment_parameters.addWidget(widget_experiment_parameters_task)

        stimulus_type = ['object', 'action', 'word', 'sound']
        selection_stimulus_type = QtWidgets.QComboBox()
        for type_ in stimulus_type:
            selection_stimulus_type.addItem(type_)
        selection_stimulus_type.setCurrentText(self.config_experiment.stimulus_type)
        layout_experiment_parameters_task.addRow("type", selection_stimulus_type)

        field_n_stimulus = QtWidgets.QLineEdit()
        field_n_stimulus.setText(str(self.config.experiment.n_stimulus))
        field_n_stimulus.textChanged.connect(partial(self.handle_field_n_stimulus_textChanged, field_n_stimulus))
        layout_experiment_parameters_task.addRow("number", field_n_stimulus)

        stimulus_difficulty = ['easy', 'hard']
        selection_stimulus_difficulty = QtWidgets.QComboBox()
        for difficulty in stimulus_difficulty:
            selection_stimulus_difficulty.addItem(difficulty)
        selection_stimulus_difficulty.setCurrentText(self.config_experiment.stimulus_difficulty)
        selection_stimulus_difficulty.currentTextChanged.connect(
            partial(self.handle_selection_stimulus_difficulty_currentTextChanged, selection_stimulus_difficulty)
        )
        layout_experiment_parameters_task.addRow("difficulty", selection_stimulus_difficulty)

        stimulus_features = [
            'subjective complexity',
            'picture familiarity',
            'noun acquisition age',
            'noun imageability',
            'noun picture agreement',
            'noun frequency'
        ]
        selection_stimulus_features = QtWidgets.QComboBox()
        for feature in stimulus_features:
            selection_stimulus_features.addItem(feature)
        # print(' '.join(self.config_experiment.stimulus_feature.split('_')))
        selection_stimulus_features.setCurrentText(' '.join(self.config_experiment.stimulus_feature.split('_')))
        selection_stimulus_features.currentTextChanged.connect(
            partial(self.handle_selection_stimulus_features_currentTextChanged, selection_stimulus_features)
        )
        layout_experiment_parameters_task.addRow("features", selection_stimulus_features)

        layout_experiment_parameters_iteration = QtWidgets.QFormLayout()
        widget_experiment_parameters_iteration = QtWidgets.QWidget()
        widget_experiment_parameters_iteration.setLayout(layout_experiment_parameters_iteration)
        # widget_experiment_parameters_iteration.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout_experiment_parameters.addWidget(widget_experiment_parameters_iteration)

        field_n_splits = QtWidgets.QLineEdit()
        field_n_splits.textChanged.connect(
            partial(self.handle_field_n_splits_textChanged, field_n_splits)
        )
        field_n_splits.setText(str(self.config.experiment.n_splits))
        layout_experiment_parameters_iteration.addRow("number of splits", field_n_splits)

        self.field_stimulus_time = QtWidgets.QLineEdit()
        # field_single_picture_time.setText(str(self.config.experiment.n_stimulus))
        self.field_stimulus_time.textChanged.connect(
            partial(self.handle_field_stimulus_time_textChanged, self.field_stimulus_time)
        )
        layout_experiment_parameters_iteration.addRow("time per stimulus (s)", self.field_stimulus_time)

        self.field_between_time = QtWidgets.QLineEdit()
        # field_between_time.setText(str(self.config.experiment.n_stimulus))
        self.field_between_time.textChanged.connect(
            partial(self.handle_field_between_time_textChanged, self.field_between_time)
        )
        layout_experiment_parameters_iteration.addRow("time between stimulus (s)", self.field_between_time)

        self.handle_selection_stimulus_type_currentTextChanged(selection_stimulus_type)
        selection_stimulus_type.currentTextChanged.connect(
            partial(self.handle_selection_stimulus_type_currentTextChanged, selection_stimulus_type)
        )

        layout_experiment_checkbox = QtWidgets.QHBoxLayout()
        widget_experiment_checkbox = QtWidgets.QWidget()
        widget_experiment_checkbox.setLayout(layout_experiment_checkbox)
        layout_experiment_parameters_iteration.addWidget(widget_experiment_checkbox)

        checkbox_random_intervals = QtWidgets.QCheckBox("random intervals")
        checkbox_random_intervals.setChecked(self.config_experiment.use_random_intervals)
        checkbox_random_intervals.stateChanged.connect(self.handle_checkbox_random_intervals_stateChanged)
        # checkbox_random_intervals.setChecked(self.config_experiment.use_random_intervals)
        layout_experiment_checkbox.addWidget(checkbox_random_intervals)

        checkbox_shuffle_stimulus = QtWidgets.QCheckBox("shuffle stimulus")
        checkbox_shuffle_stimulus.setChecked(self.config_experiment.shuffle_stimulus)
        checkbox_shuffle_stimulus.stateChanged.connect(self.handle_checkbox_shuffle_stimulus_stateChanged)
        layout_experiment_checkbox.addWidget(checkbox_shuffle_stimulus)

        widget_out_buttons = self.create_widget_out_buttons()
        layout_experiment_parameters_window.addWidget(widget_out_buttons)


    def handle_selection_stimulus_type_currentTextChanged(self, selection_stimulus_type):
        self.config_experiment.stimulus_type = selection_stimulus_type.currentText()
        for field_name, field_value in vars(self.config_experiment).items():
            if field_name == '{}_time'.format(self.config_experiment.stimulus_type):
                # print(field_name)
                self.field_stimulus_time.setText(str(field_value))
            elif field_name == 'between_{}_time'.format(self.config_experiment.stimulus_type):
                # print(field_name)
                self.field_between_time.setText(str(field_value))


    def handle_field_n_stimulus_textChanged(self, field_n_stimulus):
        self.config_experiment.n_stimulus = field_n_stimulus.text()
        # print(self.config_experiment.stimulus_type)

    def handle_selection_stimulus_difficulty_currentTextChanged(self, selection_stimulus_difficulty):
        self.config_experiment.stimulus_difficulty = selection_stimulus_difficulty.currentText()

    def handle_selection_stimulus_features_currentTextChanged(self, selection_stimulus_features):
        self.config_experiment.stimulus_feature = '_'.join(selection_stimulus_features.currentText().split())
        # print(self.config_experiment.stimulus_feature)

    def handle_field_n_splits_textChanged(self, field_n_splits):
        self.config_experiment.n_splits = field_n_splits.text()

    def handle_field_stimulus_time_textChanged(self, field_stimulus_time):
        setattr(self.config_experiment, '{}_time'.format(self.config_experiment.stimulus_type), field_stimulus_time.text())

    def handle_field_between_time_textChanged(self, field_between_time):
        setattr(self.config_experiment, 'between_{}_time'.format(self.config_experiment.stimulus_type), field_between_time.text())

    def handle_checkbox_random_intervals_stateChanged(self, state):
        self.config_experiment.use_random_intervals = state

    def handle_checkbox_shuffle_stimulus_stateChanged(self, state):
        self.config_experiment.shuffle_stimulus = state

    def create_widget_out_buttons(self):
        layout_out_buttons = QtWidgets.QHBoxLayout()
        widget_out_buttons = QtWidgets.QWidget()
        widget_out_buttons.setLayout(layout_out_buttons)

        button_experiment_parameters_save = QtWidgets.QPushButton("Save")
        button_experiment_parameters_save.clicked.connect(self.handle_clicked_button_experiment_parameters_save)
        layout_out_buttons.addWidget(button_experiment_parameters_save)

        button_experiment_parameters_cancel = QtWidgets.QPushButton("Cancel")
        button_experiment_parameters_cancel.clicked.connect(self.handle_clicked_button_experiment_parameters_cancel)
        layout_out_buttons.addWidget(button_experiment_parameters_cancel)

        button_experiment_parameters_reset = QtWidgets.QPushButton("Reset")
        button_experiment_parameters_reset.clicked.connect(self.handle_clicked_button_experiment_parameters_reset)
        layout_out_buttons.addWidget(button_experiment_parameters_reset)

        return widget_out_buttons

    def handle_clicked_button_experiment_parameters_save(self):
        for field_name, field_value in vars(self.config_experiment).items():
            self.em.trigger('update config.experiment.{}'.format(field_name), field_value)
        self.em.trigger('update config.experiment.n_stimulus_per_split')
        self.em.trigger('update selection split')
        self.em.trigger('update local.splits_values', self.stimulus)
        self.close()

    def handle_clicked_button_experiment_parameters_cancel(self):
        self.close()

    def handle_clicked_button_experiment_parameters_reset(self):
        self.config_experiment = copy.deepcopy(self.config_experiment_copy)



class SelectChannelsWindow(QtWidgets.QDialog):
    checkboxes = []

    def __init__(self, em, config):
        super().__init__()
        self.em = em
        self.config = config
        self.setWindowTitle("Select Channels")

        # self.channels_copy = np.copy(self.config.processor.channels)
        self.channels = np.copy(self.config.processor.channels)
        self.n_channels_grid = self.config.processor.n_channels_grid
        self.n_rows = self.config.processor.n_rows
        self.n_columns = self.config.processor.n_columns
        self.grid_type = self.config.processor.grid_type


        layout_select_channels_window = QtWidgets.QVBoxLayout()
        self.setLayout(layout_select_channels_window)

        widget_select_channels_button = self.create_widget_select_channels_button()
        widget_select_channels_checkbox = self.create_widget_select_channels_checkbox()

        layout_select_channels = QtWidgets.QHBoxLayout()
        layout_select_channels.addWidget(widget_select_channels_button)
        layout_select_channels.addWidget(widget_select_channels_checkbox)
        widget_select_channels = QtWidgets.QWidget()
        widget_select_channels.setLayout(layout_select_channels)

        layout_select_channels_window.addWidget(widget_select_channels)

        widget_out_buttons = self.create_widget_out_buttons()
        layout_select_channels_window.addWidget(widget_out_buttons)

    def create_widget_select_channels_button(self):
        layout_select_channels_button = QtWidgets.QVBoxLayout()
        widget_select_channels_button = QtWidgets.QWidget()
        widget_select_channels_button.setLayout(layout_select_channels_button)
        widget_select_channels_button.setFixedWidth(200)
        layout_select_channels_button.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)


        self.button_group_grid_types = QtWidgets.QButtonGroup()
        grids = {"1,1,1": "1 (1 x 1)", "20,5,4": "20 (5 x 4)", "32,8,4": "32 (8 x 4)", "64,8,8": "64 (8 x 8)"}
        for grid_type, grid_name in grids.items():
            radio_button = QtWidgets.QRadioButton(grid_name)
            radio_button.setObjectName(grid_type)
            self.button_group_grid_types.addButton(radio_button)
            layout_select_channels_button.addWidget(radio_button)

        self.button_group_grid_types.setExclusive(True)
        self.button_group_grid_types.buttonClicked.connect(self.handle_button_grid_type_buttonClicked)

        for button in self.button_group_grid_types.buttons():
            if button.objectName() == self.grid_type:
                button.setChecked(True)
                break

        self.label_n_channels = QtWidgets.QLabel(self.get_label_channel_count(self.channels, self.n_channels_grid))
        layout_select_channels_button.addWidget(self.label_n_channels)

        return widget_select_channels_button

    def handle_button_grid_type_buttonClicked(self):
        selected_button = self.button_group_grid_types.checkedButton()
        grid_type = selected_button.objectName()
        n_channels_grid, n_rows, n_columns = list(map(int, grid_type.split(',')))

        self.n_channels_grid = n_channels_grid
        self.n_rows = n_rows
        self.n_columns = n_columns
        self.grid_type = grid_type

        # for checkbox in self.checkboxes:
        #     checkbox.setChecked(False)
        for i, checkbox in enumerate(self.checkboxes):
            if i < self.n_channels_grid:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)

        self.label_n_channels.setText(self.get_label_channel_count(self.channels, self.n_channels_grid))


    def get_label_channel_count(self, channels, n_channels_grid):
        n_channels = np.sum(channels).item()
        if n_channels > n_channels_grid:
            return f'<b><font color="red">Selected {np.sum(self.channels).item()} channels out of {self.n_channels_grid}</font></b>'
        else:
            return f'Selected {np.sum(self.channels).item()} channels out of {self.n_channels_grid}'



    def create_widget_select_channels_checkbox(self):
        layout_select_channels_checkbox = QtWidgets.QGridLayout()
        widget_select_channels_checkbox = QtWidgets.QWidget()
        widget_select_channels_checkbox.setLayout(layout_select_channels_checkbox)

        self.checkboxes = []
        for i in range(8):
            for j in range(8):
                index = i * 8 + j
                checkbox = QtWidgets.QCheckBox("{}".format(index + 1))
                checkbox.stateChanged.connect(
                    lambda state, index=index: self.handle_checkbox_stateChanged(state, index))
                checkbox.setChecked(self.channels[index])
                self.checkboxes.append(checkbox)
                layout_select_channels_checkbox.addWidget(checkbox, i, j)
        return widget_select_channels_checkbox

    def create_widget_out_buttons(self):
        layout_out_buttons = QtWidgets.QHBoxLayout()
        widget_out_buttons = QtWidgets.QWidget()
        widget_out_buttons.setLayout(layout_out_buttons)

        button_channels_save = QtWidgets.QPushButton("Save")
        button_channels_save.clicked.connect(self.handle_clicked_button_channels_save)
        layout_out_buttons.addWidget(button_channels_save)

        button_channels_cancel = QtWidgets.QPushButton("Cancel")
        button_channels_cancel.clicked.connect(self.handle_clicked_button_channels_cancel)
        layout_out_buttons.addWidget(button_channels_cancel)

        button_channels_reset = QtWidgets.QPushButton("Reset")
        button_channels_reset.clicked.connect(self.handle_clicked_button_channels_reset)
        layout_out_buttons.addWidget(button_channels_reset)

        return widget_out_buttons

    def handle_clicked_button_channels_save(self):
        n_channels = np.sum(self.channels).item()
        if n_channels > self.n_channels_grid:
            return
        self.em.trigger('update config.processor.grid_type', self.grid_type)
        self.em.trigger('update config.processor.channels', self.channels)
        self.close()

    def handle_clicked_button_channels_cancel(self):
        self.close()

    def handle_clicked_button_channels_reset(self):
        # self.channels = np.copy(self.channels_copy)

        self.channels = np.copy(self.config.processor.channels)
        self.n_channels_grid = self.config.processor.n_channels_grid
        self.n_rows = self.config.processor.n_rows
        self.n_columns = self.config.processor.n_columns
        self.grid_type = self.config.processor.grid_type

        for button in self.button_group_grid_types.buttons():
            # print(button.objectName(), self.grid_type)
            if button.objectName() == self.grid_type:
                button.setChecked(True)
                break

        for i, checkbox in enumerate(self.checkboxes):
            checkbox.setChecked(self.channels[i])
        self.label_n_channels.setText(self.get_label_channel_count(self.channels, self.n_channels_grid))


    def handle_checkbox_stateChanged(self, state, index):
        self.channels[index] = state
        self.label_n_channels.setText(self.get_label_channel_count(self.channels, self.n_channels_grid))



class ExperimentWindow(QtWidgets.QDialog):
    def __init__(self,config, em, experiment):
        super().__init__()
        self.config = config
        self.em = em
        self.experiment = experiment
        self.timer_connection = QtCore.QTimer(self)
        self.connection_status = False

        layout_experiment = QtWidgets.QVBoxLayout()
        self.setLayout(layout_experiment)
        self.setWindowTitle("ELOQ Settings")

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout_experiment.addWidget(separator)

        # label_experiment = QtWidgets.QLabel("Experiment")
        # label_experiment.setObjectName("experiment_label")
        # layout_experiment.addWidget(label_experiment)

        layout_connection_status = QtWidgets.QFormLayout()
        widget_connection_status = QtWidgets.QWidget()
        widget_connection_status.setLayout(layout_connection_status)
        layout_experiment.addWidget(widget_connection_status)
        connection_status = QtWidgets.QLabel("Please Wait...")
        self.timer_connection.timeout.connect(lambda : self.update_connection_status(connection_status))
        self.timer_connection.start(100)

        layout_connection_status.addRow("connection status", connection_status)

        button_experiment_start = QtWidgets.QPushButton("Connect")
        button_experiment_start.setObjectName("start_button")
        button_experiment_start.setCheckable(True)

        if not self.experiment.process:
            button_experiment_start.setStyleSheet("")
            button_experiment_start.setChecked(False)
            button_experiment_start.setText("Connect")
        else:
            print(self.experiment.process)
            button_experiment_start.setChecked(True)
            button_experiment_start.setStyleSheet("background-color: blue; color: white;")
            button_experiment_start.setText("Disconnect")

        button_experiment_start.toggled.connect(
            partial(self.handle_button_experiment_start, button_experiment_start, layout_experiment)
        )
        layout_experiment.addWidget(button_experiment_start)

    def update_connection_status(self, label):
        #current_color = self.label.palette().color(QPalette.WindowText)
        #new_color = Qt.green if current_color == Qt.red else Qt.red
        if (self.connection_status):
            label.setText("Connected")
            label.setStyleSheet("color: green")
        else:
            label.setText("Disconnected")
            label.setStyleSheet("color: red")

    def handle_button_experiment_start(self, button, layout, checked):
        if checked:
            button.setStyleSheet("background-color: blue; color: white;")
            button.setText("Disconnect")

            self.experiment.start()
            self.connection_status = True
            button.setStyleSheet("background-color: blue; color: white;")
            button.setText("Disconnect")
        else:
            self.experiment.clear()
            self.connection_status = False
            button.setStyleSheet("")
            button.setText("Connect")


class PatientWindow(QtWidgets.QDialog):
    def __init__(self, config, em):
        super().__init__()
        self.config = config
        self.em = em

        layout_patient_info = QtWidgets.QVBoxLayout()
        # widget_patient_info = QtWidgets.QWidget()
        self.setLayout(layout_patient_info)
        self.setWindowTitle("Patient Settings")

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout_patient_info.addWidget(separator)

        label_patient_name = QtWidgets.QLabel("Patient Info")
        layout_patient_info.addWidget(label_patient_name)

        layout_patient_values = QtWidgets.QFormLayout()
        widget_patient_values = QtWidgets.QWidget()

        widget_patient_values.setLayout(layout_patient_values)
        layout_patient_info.addWidget(widget_patient_values)

        line_patient_name = QtWidgets.QLineEdit()
        line_patient_name.setText(str(self.config.patient_info.patient_name))  # (self.config.patient_info.patient_name)
        line_patient_name.textChanged.connect(partial(self.handle_patient_name_textChanged, line_patient_name))

        line_patient_birth_date = QtWidgets.QLineEdit(str(self.config.patient_info.patient_date))
        line_patient_hospital = QtWidgets.QLineEdit(str(self.config.patient_info.patient_hospital))

        line_patient_historyID = QtWidgets.QLineEdit(str(self.config.patient_info.patient_history_id))
        line_patient_hospitalization_date = QtWidgets.QLineEdit(
            str(self.config.patient_info.patient_hospitalization_date))

        layout_patient_values.addRow("name", line_patient_name)
        layout_patient_values.addRow("birth date", line_patient_birth_date)
        layout_patient_values.addRow("hospital", line_patient_hospital)
        layout_patient_values.addRow("historyID", line_patient_historyID)
        layout_patient_values.addRow("hospitalization date", line_patient_hospitalization_date)

        line_patient_data_path = QtWidgets.QLineEdit()
        line_patient_data_path.setText(str(self.config.paths.patient_data_path))
        line_patient_data_path.setEnabled(False)
        # line_patient_data_path.textChanged.connect(partial(self.handle_patient_name_textChanged, line_patient_data_path))
        layout_patient_values.addRow("patient data", line_patient_data_path)

    def handle_patient_name_textChanged(self, line_patient_name):
        self.em.trigger('update config.patient_info.patient_name', line_patient_name.text())



class ReceiverWindow(QtWidgets.QDialog):
    def __init__(self, config, em, receiver, generator_lsl, record_lsl, experiment, processor, timeseries, sound, timer_connect, control_widget):
        super().__init__()
        self.setWindowTitle("LSL Settings")
        self.config = config
        self.em = em
        self.receiver = receiver
        self.processor = processor
        self.timeseries = timeseries
        self.sound = sound
        self.generator_lsl = generator_lsl
        self.record_lsl = record_lsl
        self.experiment = experiment
        self.timer_connect = timer_connect  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        self.control_widget = control_widget
        
        layout_receiver = QtWidgets.QVBoxLayout()
        self.setLayout(layout_receiver)
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout_receiver.addWidget(separator)

        self.button_generator_lsl = QtWidgets.QPushButton("GeneratorLSL")
        self.button_generator_lsl.setObjectName('button_generator_lsl')
        self.button_generator_lsl.setCheckable(True)
        self.button_generator_lsl.setChecked(False)
        self.button_generator_lsl.toggled.connect(partial(self.handle_button_generator_lsl, self.button_generator_lsl))
        layout_receiver.addWidget(self.button_generator_lsl)
        self.button_generator_lsl_locked = False

        self.button_record_lsl = QtWidgets.QPushButton("RecordLSL")
        self.button_record_lsl.setObjectName('button_record_lsl')
        self.button_record_lsl.setCheckable(True)
        self.button_record_lsl.setChecked(False)
        self.button_record_lsl.toggled.connect(partial(self.handle_button_record_lsl, self.button_record_lsl))
        layout_receiver.addWidget(self.button_record_lsl)
        self.button_record_lsl_locked = False

        form_layout = QtWidgets.QFormLayout()
        form_widget = QtWidgets.QWidget()
        form_widget.setLayout(form_layout)
        layout_receiver.addWidget(form_widget)

        self.amplifiers = []
        self.amplifiers.append(self.config.receiver.amplifier)
        self.amplifiers.append(self.config.receiver.lsl_stream_name_generator)
        self.amplifiers.append(self.config.receiver.lsl_stream_name_record)

        selection_amplifier = QtWidgets.QComboBox()
        for amplifier in self.amplifiers:
            selection_amplifier.addItem(amplifier)
        field_ip_address = QtWidgets.QLineEdit()
        selection_amplifier.currentTextChanged.connect(
            partial(self.handle_currentTextChanged_amplifier, field_ip_address, selection_amplifier)
        )
        form_layout.addRow("Amp", selection_amplifier)

        selected_amplifier = selection_amplifier.currentText()
        field_ip_address.setText(self.config.receiver.amplifier_ip)
        if selected_amplifier != "EBNeuro_BePLusLTM":
            field_ip_address.setVisible(False)
        field_ip_address.textChanged.connect(partial(self.handle_textChanged_ip_address, field_ip_address))
        form_layout.addRow("IP", field_ip_address)

        field_fs = QtWidgets.QLineEdit()
        field_fs.setText(str(self.config.receiver.fs))
        field_fs.textChanged.connect(partial(self.handle_textChanged_fs, field_fs))
        form_layout.addRow("fs", field_fs)

        button_select_channels = QtWidgets.QPushButton("Select Channels")
        button_select_channels.clicked.connect(
            partial(self.handle_button_select_channels_clicked, button_select_channels, self)
        )
        layout_receiver.addWidget(button_select_channels)

        button_connect = QtWidgets.QPushButton("Connect")
        #button_connect.setStyleSheet("background-color: black; color: white")
        button_connect.setObjectName("connect_button")
        button_connect.setCheckable(True)

        if not self.receiver.process:
            button_connect.setStyleSheet("") 
            button_connect.setChecked(False)
        else:
            button_connect.setChecked(True)
            self.button_generator_lsl.setDisabled(True)
            self.button_record_lsl.setDisabled(True)
            button_connect.setStyleSheet("background-color: blue; color: white;")

        if not self.generator_lsl.process:
            self.button_generator_lsl.setStyleSheet("")
            self.button_generator_lsl.setChecked(False)
        else:
            self.button_generator_lsl.setChecked(True)
            self.button_generator_lsl.setStyleSheet("background-color: blue; color: white;")

        if not self.record_lsl.process:
            self.button_record_lsl.setStyleSheet("")
            self.button_record_lsl.setChecked(False)
        else:
            self.button_record_lsl.setChecked(True)
            self.button_record_lsl.setStyleSheet("background-color: blue; color: white;")

        button_connect.toggled.connect(partial(self.handle_button_connect, button_connect, layout_receiver))
        layout_receiver.addWidget(button_connect)

        #return widget_receiver
        

    def handle_button_generator_lsl(self, button, checked):
        if checked:
            button.setStyleSheet("background-color: blue; color: white;")
            self.generator_lsl.start()
            self.button_record_lsl.setDisabled(True)
            self.button_record_lsl_locked = True
        else:
            button.setStyleSheet("")
            self.generator_lsl.clear()
            self.button_record_lsl.setEnabled(True)
            self.button_record_lsl_locked = False


    def handle_button_record_lsl(self, button, checked):
        if checked:
            button.setStyleSheet("background-color: blue; color: white;")
            self.record_lsl.start()
            self.button_generator_lsl.setDisabled(True)
            self.button_generator_lsl_locked = True
        else:
            button.setStyleSheet("")
            self.record_lsl.clear()
            self.button_generator_lsl.setEnabled(True)
            self.button_generator_lsl_locked = False



    def handle_button_connect(self, button, layout, checked):
        if checked:
            self.control_widget.get_start_icon().setIcon(QIcon("../resource/icons/pause.svg"))
            button.setStyleSheet("background-color: blue; color: white;")
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if widget.objectName() not in ["connect_button", 'receiver_label']:
                    widget.setDisabled(True)
            print("connect")
            self.em.trigger('receiver.connect')

            # from eloq_server import callback_patient, callback_start, PatientData
            # patient_data = PatientData(
            #     name='test_subject',
            #     birthDate='01.01.0001',
            #     hospital='Princeton-Plainsboro',
            #     historyID='Unknown',
            #     hospitalizationDate='01.01.2001',
            # )
            # callback_patient(self.experiment.queue, patient_data)
            # callback_start(self.experiment.queue, None)

            self.timer_connect.timeout.connect(
                partial(self.processor.on_timer, self.timeseries.update_data, self.sound.update_data)
            )
            self.timer_connect.start(30)
        else:
            from eloq_server import callback_finish

            self.control_widget.get_start_icon().setIcon(QIcon("../resource/icons/start.svg"))
            button.setStyleSheet("")
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if widget.objectName() not in ["connect_button", 'receiver_label']:
                    widget.setEnabled(True)
                if widget.objectName() == 'button_record_lsl' and self.button_record_lsl_locked:
                    widget.setDisabled(True)
                elif widget.objectName() == 'button_generator_lsl' and self.button_generator_lsl_locked:
                    widget.setDisabled(True)

            callback_finish(self.experiment.queue, None)

            self.timer_connect.stop()
            print("terminate")
            self.receiver.clear()

    
    def handle_currentTextChanged_amplifier(self, field_ip_address, amplifier):
        if amplifier.currentText() == "EBNeuro_BePLusLTM":
            field_ip_address.setVisible(True)
        else:
            field_ip_address.setVisible(False)
        # self.config.receiver.update_amplifier(self.em, amplifier.currentText())
        # print('handle_currentTextChanged_amplifier')
        self.em.trigger('update config.receiver.amplifier', amplifier.currentText())
        # print(self.em.handlers['update config.receiver.amplifier'])
    
    def handle_textChanged_ip_address(self, ip_address):
        # self.config.receiver.update_amplifier_ip(ip_address.text())
        self.em.trigger('update config.receiver.amplifier_ip', ip_address.text())

    def handle_textChanged_fs(self, fs):
        # self.config.receiver.update_fs(self.em, fs.text())
        self.em.trigger('update config.receiver.fs', fs.text())

    def handle_button_select_channels_clicked(self, button, widget):
        select_channels_window = SelectChannelsWindow(self.em, self.config)
        select_channels_window.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        x = widget.geometry().x() + widget.geometry().width()
        # y = button.geometry().y() + int(select_channels_window.geometry().height() / 2)
        y = widget.geometry().y()
        select_channels_window.move(x, y)
        select_channels_window.setWindowFlags(
            select_channels_window.windowFlags() | QtCore.Qt.WindowType.CustomizeWindowHint)
        select_channels_window.setWindowFlags(
            select_channels_window.windowFlags() & ~QtCore.Qt.WindowType.WindowCloseButtonHint)
        select_channels_window.exec()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())
