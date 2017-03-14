#!/usr/bin/env python3

import sys
import os
import glob
import numpy as np
from IPython import embed
from collections import OrderedDict
from optparse import OptionParser
from datetime import date, datetime, timedelta
from VideoRecording import VideoRecording
from VideoCanvas import VideoCanvas
from MetadataTab import MetadataTab
from CamControllerTab import CamControllerTab
from RasPiCamControllerTab import RasPiCamControllerTab
from Camera import Camera, bgr2rgb, bgr2grayscale
from default_config import default_template, camera_device_search_range, camera_name_format, frames_per_second, \
    width, height, max_tab_width, min_tab_width, offset_left, offset_top
from doc import doc


# from PIL import Image as image
# from PIL import ImageQt as iqt
# from nitime.index_utils import tri
# from MetadataEntry import MetadataEntry

__author__ = 'Joerg Henninger, Jan Grewe, Fabian Sinz, Lorand, Janez Presern'

sys.path.append('../')

# #######################################
'''
Note:
QMainWindow allows for funky things like menu- and tool-bars

Keyboard Shortcuts:
# Quit Program: ESC # doesn't work properly
# Starts/stops recording: ALT + Space
# Adds tag: ALT + T # doesn't work properly
# Cancels recording: ALT + C
# Idle videocanvas: SHIFT + I
# Next Metadata-Tab: CTRL+Page-Down
# Previous Metadata-Tab: CTRL+Page-UP


== OPTIONS ==
-u --template           -- choose your template by its name
-k --stop_time          -- define a stop time for your recording; Formats: "HH:MM:SS" and "YY-mm-dd HH:MM:SS"
-l --recording_length   -- define recording length
-o --output_directory   -- define the output directory of your recordings
-s --instant_start      -- start the recording instantly without user input
-i --idle_screen        -- do not display the video frames; this saves quite some computational power
-c --color              -- record in color
-e --segmentation       -- segment recording into short files; enter duration of segment. Format: "HH:MM:SS"
'''

# #######################################
# TODO: check RaspiCamController tabs. They are currently disabled.
# TODO: PgUp/PgDown actions doens't change the tab, but chrashes it. why?
# TODO video-canvas: full screen does not work properly. why?
# TODO validation of meta data tabs. Warn, if info is missing!
# TODO: BW (gray scale) support now hacked via tripling the gray scale values to imitate RGB. Probably local codec issue
# TODO: add sound?
# TODO: add help

# ########################################

try:
    from PyQt5 import QtGui, QtCore, QtWidgets
    from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
except:
    print('Unfortunately, your system misses the PyQt5 packages.')
    quit()


try:
    import odml
except:
    sys.path.append('/usr/lib/python3.5.1/site-packages')
    try:
        import odml
    except:
        print('Cannot import odML library for metadata support! Check https://github.com/G-Node/python-odml')
        quit()

# #######################################
# THE MAIN GUI WINDOW


class Main(QtWidgets.QMainWindow):

    sig = pyqtSignal(int)

    def __init__(self, app, options=None, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        try:
            global RasPiCam
            from RasPiCam import RasPiCam
            self.picam_packages_loaded = True
            global RasPiVideoRecording
            from RasPiVideoRecording import RasPiVideoRecording
        except:
            self.picam_packages_loaded = False
            print("Picamera Packages not installed. PiCamera not available.")

        # self.picam_packages_loaded = False

        self.app = app
        self.metadata_tabs = dict()
        self.trial_counter = 0
        self.output_dir = '.'
        self.data_dir = '.'
        self.event_list = None
        self.record_timestamp = None
        self.color = False
        self.cameras = None
        # #######################################
        self.setGeometry(offset_left, offset_top, width, height)
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.setMinimumSize(width, height)
        self.setWindowTitle('Video GUI')

        # #######################################

        # self.video_recordings = OrderedDict()

        # #######################################
        # HANDLE OPTIONS

        self.default_xml_template = default_template
        self.idle_screen = False
        self.instant_start = False
        self.programmed_stop = False
        self.programmed_stop_datetime = None
        self.start_time = None
        self.programmed_segmentation = False
        self.programmed_segmentation_datetime = None
        self.programmed_recording_length = False
        self.programmed_recording_length_datetime = False

        if options:
            # template selection
            if options.template:
                template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
                optional_template = os.path.join(template_path, options.template)
                if os.path.exists(optional_template):
                    self.default_xml_template = optional_template
                    print('Template chosen: {0:s}'.format(os.path.basename(self.default_xml_template)))
                else:
                    print('Error: chosen template does not exist')
                    quit()

            # programmed stop-time
            if options.stop_time:
                try:
                    a = datetime.strptime(options.stop_time, '%H:%M:%S')
                    b = datetime.now()
                    c = datetime(b.year, b.month, b.day, a.hour, a.minute, a.second)
                    if c < b:
                        c += timedelta(days=1)
                except ValueError:
                    pass
                else:
                    self.programmed_stop = True
                    self.programmed_stop_datetime = c

                try:
                    a = datetime.strptime(options.stop_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
                else:
                    self.programmed_stop = True
                    self.programmed_stop_datetime = a

                if self.programmed_stop is not True:
                    print('Error: allowed stop-time formats are:' '\n"HH:MM:SS" and "YY-mm-dd HH:MM:SS"')
                    quit()
                else:
                    print('Automated Stop activated: {0:s}'.format(str(self.programmed_stop_datetime)))

            # output directory
            if options.output_dir:
                if os.path.exists(options.output_dir):
                    self.output_dir = os.path.realpath(options.output_dir)
                    print(self.output_dir)
                    print('Output Directory: {0:s}'.format(self.output_dir))
                else:
                    print('Error: output directory does not exist')
                    quit()

            # instant start and idle_screen
            self.instant_start = options.instant_start
            if self.instant_start:
                print('Instant Start: ON')

            self.idle_screen = options.idle_screen
            if self.idle_screen:
                print('Video Display OFF')

            # color recording
            if options.color:
                self.color = True
                print('Recording in color')

            # programmed stop-time
            if options.segmentation:
                try:
                    a = datetime.strptime(options.segmentation, '%H:%M:%S')
                    c = datetime(a.year, a.month, a.day, a.hour, a.minute, a.second)

                except ValueError:
                    pass
                else:
                    self.programmed_segmentation = True
                    self.programmed_segmentation_datetime = c

                if self.programmed_segmentation is not True:
                    print('Error: allowed stop-time formats are:' '\n"HH:MM:SS" and "YY-mm-dd HH:MM:SS"')
                    quit()
                else:
                    print('Automated segmentation activated: {0:s}'.format(str(self.programmed_segmentation_datetime)))

            if options.recording_length:
                try:
                    a = datetime.strptime(options.recording_length, '%H:%M:%S')
                    c = datetime(a.year, a.month, a.day, a.hour, a.minute, a.second)

                except ValueError:
                    pass
                else:
                    self.programmed_recording_length = True
                    self.programmed_recording_length_datetime = c

                if self.programmed_recording_length is not True:
                    print('Error: allowed stop-time formats are:' '\n"HH:MM:SS" and "YY-mm-dd HH:MM:SS"')
                    quit()
                else:
                    print('Recording length set: {0:s}'.format(str(self.programmed_recording_length_datetime)))

        # self.init_layouts()
        # self.init_UI_action()

    # def init_layouts(self):

        self.init_layout()
        self.create_menu_bar()
        self.init_ui_action()
        # #######################################
        # LAYOUTS
    def init_layout(self):

        self.main = QtWidgets.QWidget()
        self.setCentralWidget(self.main)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main.setLayout(self.main_layout)

        self.top_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_info_layout = QtWidgets.QHBoxLayout()

        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.addLayout(self.bottom_info_layout)

        # #######################################
        #  TOP LAYOUT
        self.videos = QtWidgets.QTabWidget()
        self.videos.setMinimumWidth(min_tab_width)
        self.videos.setMaximumWidth(max_tab_width)
        self.video_recordings = None
        self.video_tabs = {}

        self.controller = QtWidgets.QTabWidget()
        self.controller.setMinimumWidth(min_tab_width)
        self.controller.setMaximumWidth(max_tab_width)

        self.metadata = QtWidgets.QTabWidget()
        self.metadata.setMinimumWidth(min_tab_width)
        self.metadata.setMaximumWidth(max_tab_width)

        self.top_layout.addWidget(self.videos)
        self.top_layout.addWidget(self.controller)
        self.top_layout.addWidget(self.metadata)

        # #######################################
        # POPULATE TAB
        default_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates', self.default_xml_template)
        self.populate_metadata_tab(default_template_path)
        self.populate_video_tabs()
        self.populate_controller_tabs()

        # #######################################
        # POPULATE BOTTOM LAYOUT
        self.button_record = QtWidgets.QPushButton('Start Recording')
        self.button_stop = QtWidgets.QPushButton('Stop')
        self.button_cancel = QtWidgets.QPushButton('Cancel')
        self.button_tag = QtWidgets.QPushButton('&Tag')
        self.button_idle = QtWidgets.QPushButton('Idle Screen')

        self.button_stop.setDisabled(True)
        self.button_cancel.setDisabled(True)
        self.button_tag.setDisabled(True)

        self.button_record.setMinimumHeight(50)
        self.button_stop.setMinimumHeight(50)
        self.button_cancel.setMinimumHeight(50)
        self.button_tag.setMinimumHeight(50)
        self.button_idle.setMinimumHeight(50)

        self.bottom_layout.addWidget(self.button_record)
        self.bottom_layout.addWidget(self.button_stop)
        self.bottom_layout.addWidget(self.button_cancel)
        self.bottom_layout.addWidget(self.button_tag)
        self.bottom_layout.addWidget(self.button_idle)

        self.label_time = QtWidgets.QLabel('', self)
        font = self.label_time.font()
        font.setPointSize(18)
        self.label_time.setFont(font)

        self.bottom_info_layout.addStretch(0)
        self.bottom_info_layout.addWidget(self.label_time)
        self.bottom_info_layout.addStretch(0)

        # #######################################
        # self.create_menu_bar()
        # #######################################
        # WORKER THREADS
        # For heavy duty work, which might block the GUI.
        # Some typical applications are examplified.
        # Often, these processes act on different time-scales.

        # # INITIATE WORKER COMPONENTS
        # self.controlcenter = ControlCenter()
        # self.datacollector = DataCollector()
        # self.storage = Storage()
        #
        # # CREATE THREADS TO MANAGE THE COMPONENTS
        # self.threads = dict()
        # self.threads['control'] = QtCore.QThread(self)
        # self.threads['data'] = QtCore.QThread(self)
        # self.threads['storage'] = QtCore.QThread(self)
        #
        # # MOVE COMPONENTS INTO THEIR THREADS
        # self.controlcenter.moveToThread(self.threads['control'])
        # self.datacollector.moveToThread(self.threads['data'])
        # self.storage.moveToThread(self.threads['storage'])
        #
        # # HERE, WE START THREADS, NOT THE INSTANCES INSIDE !!
        # self.threads['control'].start()
        # self.threads['data'].start()
        # self.threads['storage'].start()

        # #######################################
        # CONNECTIONS
        # These are necessary to connect GUI elements and instances in various threads.
        # Signals and slots can easily be custom-crafted to meet the needs. Data can be sent easily, too.

    def init_ui_action(self):
        # connect buttons
        self.button_cancel.clicked.connect(self.clicked_cancel)
        self.button_record.clicked.connect(self.clicked_record)
        self.button_stop.clicked.connect(self.clicked_stop)
        self.button_tag.clicked.connect(self.clicked_tag)
        self.button_idle.clicked.connect(self.clicked_idle)

        # create keyboard shortcuts
        self.action_cancel = QtWidgets.QAction("Cancel Recording", self)
        # self.action_cancel.setShortcut(QtCore.Qt.Key_Escape)
        self.action_cancel.setShortcut(QtCore.Qt.ALT + QtCore.Qt.Key_C)
        self.action_cancel.triggered.connect(self.clicked_cancel, no_receiver_check=True)
        self.addAction(self.action_cancel)

        # Create a start stop action
        self.action_start_stop = QtWidgets.QAction('Start, stop recording', self)
        # self.action_start_stop.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_Space)
        self.action_start_stop.setShortcut(QtCore.Qt.ALT + QtCore.Qt.Key_Space)
        self.action_start_stop.triggered.connect(self.start_stop, no_receiver_check=True)
        self.addAction(self.action_start_stop)

        # Create a Tag
        self.action_tag = QtWidgets.QAction('Tag Movie', self)
        self.action_tag.setShortcut(QtCore.Qt.ALT + QtCore.Qt.Key_T)
        self.action_tag.triggered.connect(self.clicked_tag, no_receiver_check=True)
        self.addAction(self.action_tag)

        # Create idle
        self.action_idle = QtWidgets.QAction('Idle screen', self)
        self.action_idle.setShortcut(QtCore.Qt.SHIFT + QtCore.Qt.Key_I)
        self.action_idle.triggered.connect(self.clicked_idle, no_receiver_check=True)
        self.addAction(self.action_idle)

        # #   TODO: changing tabs by CTRL Key_PageDown does't work
        # #   TODO: changing tabs by Key_PageDown chrashes the app
        # # # Change Tabs
        # self.action_change_tab_left = QtWidgets.QAction("Go one tab to the right", self)
        # # self.action_change_tab_left.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_PageDown)
        # # self.action_change_tab_left.setShortcut(QtCore.Qt.Key_PageDown)
        # self.action_change_tab_left.setShortcut(QtCore.Qt.ALT + QtCore.Qt.Key_Left)
        # self.action_change_tab_left.triggered.connect(self.next_tab, no_receiver_check = True)
        # self.addAction(self.action_change_tab_left)
        #
        # self.action_change_tab_right = QtWidgets.QAction("Go one tab to the left", self)
        # # self.action_change_tab_right.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_PageUp)
        # # self.action_change_tab_right.setShortcut(QtCore.Qt.Key_PageUp)
        # self.action_change_tab_right.setShortcut(QtCore.Qt.ALT + QtCore.Qt.Key_Right)
        # self.action_change_tab_right.triggered.connect(self.prev_tab, no_receiver_check = True)
        # self.addAction(self.action_change_tab_right)

        # instant start
        if self.instant_start:
            self.clicked_record()

        # a simple timer to create some noise on the canvas
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_video)
        self.timer.start(1000./frames_per_second)

    def create_menu_bar(self):
        self.statusBar()

        # exit_action = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action = QtWidgets.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QtWidgets.qApp.quit)

        template_select_action = QtWidgets.QAction('&Select template', self)
        template_select_action.setStatusTip('Select metadata template')
        template_select_action.triggered.connect(self.select_template)

        about_action = QtWidgets.QAction('&About', self)
        about_action.setStatusTip('About videoRecorder')
        about_action.triggered.connect(self.show_about)

        cam_config_action = QtWidgets.QAction('&Camera config', self)
        cam_config_action.setStatusTip('Set camera aliases')
        cam_config_action.triggered.connect(self.cam_aliases)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)
        config_menu = menu_bar.addMenu('&Configuration')
        config_menu.addAction(template_select_action)
        config_menu.addAction(cam_config_action)
        help_menu = menu_bar.addMenu('&Help')
        help_menu.addAction(about_action)

        # #######################################
        # #######################################

    def select_template(self):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
        if not os.path.isdir(path):
            path = os.path.abspath('.')
        # print("do tu")
        file_name = QtWidgets.QFileDialog().getOpenFileName(self, 'Open template', path, "XML files (*.xml *.odml)")
        # print("do tu")
        if file_name:
            self.populate_metadata_tab(file_name)

    def cam_aliases(self):
        pass

    def show_about(self):
        #TODO implement this method which shows a new window
        print('show about dialog')
        pass

    def populate_metadata_tab(self, template):
        try:
            temp = odml.tools.xmlparser.load(template)
        except:
            print('failed to load metadata template! {0}'.format(template))
            return
        self.metadata_tabs.clear()
        self.metadata.clear()
        for s in temp.sections:
            self.metadata_tabs[s.type] = MetadataTab(s, self.metadata)

    def populate_controller_tabs(self):
        if len(self.cameras) > 0:
            for cam_name, cam in list(self.cameras.items()):
                if cam.is_raspicam():
                    new_controller_tab = RasPiCamControllerTab(cam)
                    self.controller.addTab(new_controller_tab, cam_name + " - Controller")
                # else:
                #     new_controller_tab = CamControllerTab(cam)
                #     self.controller.addTab(new_controller_tab, cam_name + " - Controller")

        if len([cam for cam in self.cameras if self.cameras[cam].is_raspicam()]) == 0:
            self.top_layout.removeWidget(self.controller)
            self.controller.deleteLater()
            self.controler = None

    def populate_video_tabs(self):

       #  try:
       #     tmp = [cam for cam in [Camera(i) for i in camera_device_search_range] if cam.is_working()]
       #  except:
       #     tmp = [raspicam]
       #
       # if self.picam_packages_loaded:
       #     raspicam = RasPiCam()
       #     if raspicam.is_working():
       #         tmp.extend([raspicam])

        if self.picam_packages_loaded:
            raspicam = RasPiCam()
            if raspicam.is_working():
                tmp = [raspicam]
                # embed()
        else:
            tmp = [cam for cam in [Camera(i) for i in camera_device_search_range] if cam.is_working()]    
            
        self.cameras = {camera_name_format % j: v for j, v in enumerate(tmp)}

        if len(self.cameras) > 0:
            for cam_name, cam in self.cameras.items():
                self.video_tabs[cam_name] = VideoCanvas(parent=self)
                self.videos.addTab(self.video_tabs[cam_name], cam_name)
                self.video_tabs[cam_name].setLayout(QtWidgets.QHBoxLayout())
        else:
            self.videos.addTab(QtWidgets.QWidget(), "No camera found")

    def create_and_start_new_videorecordings(self):
        # @jan: could choose potentially from PIM1, MJPG, MP42, DIV3, DIVX, U263, I263, FLV1
        # works @ mac:  MJPG/.avi
        # works @ mac:  mp4v/.mp4
        #
        # CV_FOURCC('P','I','M','1')    = MPEG-1 codec
        if self.trial_counter == 0:
            self.check_data_dir()

        trial_name = '{0:s}/trial_{1:04d}'.format(self.data_dir, self.trial_counter)
        self.tags = list()
        self.video_recordings = OrderedDict()
        # self.video_recordings = {cam_name: (VideoRecording('{0}_{1}.mp4'.format(trial_name, cam_name),
        #                                                    '{0}_{1}_metadata.dat'.format(trial_name, cam_name),
        #                                                    cam.get_resolution(),
        #                                                    frames_per_second,
        #                                                    'mp4v',
        #                                                    color=True)
        #                                     if not cam.is_raspicam() else
        #                                     RasPiVideoRecording('{0}_{1}.h264'.format(trial_name, cam_name),
        #                                                         '{0}_{1}_metadata.dat'.format(trial_name, cam_name),
        #                                                         'h264',
        #                                                         self.cameras[cam_name]))
        #                          for cam_name, cam in self.cameras.items()}
        """ Ordered dict instead of normal dict to keep cameras in the same order"""
        for cam_name, cam in self.cameras.items():
            if cam.is_raspicam():
                self.video_recordings[cam_name] = RasPiVideoRecording('{0}_{1}.h264'.format(trial_name, cam_name),
                                                                      '{0}_{1}_metadata.dat'.format(trial_name, cam_name),
                                                                      'h264', self.cameras[cam_name])
            else:
                self.video_recordings[cam_name] = VideoRecording('{0}_{1}.avi'.format(trial_name, cam_name),
                                                                  '{0}_{1}_metadata.dat'.format(trial_name, cam_name),
                                                                  cam.get_resolution(), frames_per_second, 'MJPG',
                                                                  color=True)


        print(self.video_recordings)

        """ drop timestamp for start or recording """
        trial_info_filename = '{0:s}/trial_{1:04d}_info.dat'.format(self.data_dir, self.trial_counter)
        self.start_time = datetime.now()
        timestamp = self.start_time.strftime("%Y-%m-%d  %H:%M:%S:%f")[:-3]
        with open(trial_info_filename, 'w') as f:
            f.write("start-time:" + "\t" + timestamp + "\n")

        """ display start time """
        time_label = 'start-time: {0:s}   ---  running: {1:s}'.format(timestamp, str(datetime.now() - self.start_time)[:-7])
        self.label_time.setText(time_label)

    def check_data_dir(self):
        today = date.today()
        today_str = today.isoformat()
        self.data_dir = os.path.join(self.output_dir, today_str)
        try:
            os.mkdir(self.data_dir)
            self.trial_counter = 0
        except:
            tmp = os.listdir(self.data_dir)
            if len(tmp) > 0:
                self.trial_counter = np.amax([int(e.split('_')[1]) for e in [ee.split('.')[0] for ee in tmp]])+1

    def stop_all_recordings(self):
        """ drop timestamp for stop """
        trial_info_filename = '{0:s}/trial_{1:04d}_info.dat'.format(self.data_dir, self.trial_counter)
        with open(trial_info_filename, 'a') as f:
            timestamp = datetime.now().strftime("stop-time:" + "\t" + "%Y-%m-%d  %H:%M:%S:%f"[:-3])
            f.write(timestamp+'\n')

        for v in list(self.video_recordings.values()):
            v.stop()
        self.video_recordings = None

        self.label_time.setText('')
        self.start_time = None

    def start_stop(self):
        if self.is_recording:
            self.clicked_stop()
        else:
            self.clicked_record()

    def clicked_record(self):
        self.record_timestamp = str(datetime.now()).split('.')[0]
        self.create_and_start_new_videorecordings()
        self.button_record.setDisabled(True)
        self.button_cancel.setEnabled(True)
        self.button_tag.setEnabled(True)
        self.button_stop.setDisabled(False)
        self.event_list = odml.Section('events', 'event_list')

    def clicked_cancel(self):
        self.clicked_stop()
        trial_name = 'trial_{0:04d}'.format(self.trial_counter-1)
        list(map(os.remove, glob.glob(self.data_dir+'/'+trial_name+'*')))
        self.check_data_dir()
        self.button_cancel.setEnabled(False)
        self.button_tag.setEnabled(False)

    def clicked_stop(self):
        self.stop_all_recordings()
        self.button_record.setDisabled(False)
        self.button_stop.setDisabled(True)
        self.button_cancel.setDisabled(True)
        self.button_tag.setDisabled(True)
        self.save_metadata()
        self.trial_counter += 1

    def clicked_tag(self):
        ts = str(datetime.now()).split('.')[0]
        text, ok = QtWidgets.QInputDialog.getText(self, 'Tag data with Event', 'Enter tag comment:')
        """ write tags into .xml (odML) file """
        if ok:
            tag_name = 'event_{0:02d}'.format(len(self.event_list))
            e = odml.Section(tag_name, 'event')
            e.append(odml.Property('timestamp', odml.Value(ts, dtype='datetime')))
            e.append(odml.Property('comment', odml.Value(text, dtype='string')))
            self.event_list.append(e)
        """ write tags into the .dat file as pure text """
        trial_info_filename = '{0:s}/trial_{1:04d}_info.dat'.format(self.data_dir, self.trial_counter)
        with open(trial_info_filename, 'a') as f:
            timestamp = datetime.now().strftime(("tag-time:" + "\t" + "%Y-%m-%d  %H:%M:%S:%f")[:-3] + "\t" + text)
            f.write(timestamp + '\n')

    def clicked_idle(self):
        if self.idle_screen:
            self.idle_screen = False
        else:
            self.idle_screen = True
            # set idle screen
            for cam_name, cam in list(self.cameras.items()):
                canvas_h = self.video_tabs[cam_name].canvas_h
                canvas_w = self.video_tabs[cam_name].canvas_w
                # img = image.fromarray(np.zeros((canvas_h, canvas_w))).convert('RGB')
                # self.video_tabs[cam_name].setImage(QtGui.QImage(iqt.ImageQt(img)))

                img = np.zeros((canvas_h, canvas_w, 3))
                img = QtGui.QImage(img.data, canvas_w, canvas_h,
                                   canvas_w * 3, QtGui.QImage.Format_RGB888)
                self.video_tabs[cam_name].setImage(QtGui.QPixmap(img))

                # self.video_tabs[cam_name].setImage(QtGui.QPixmap.fromImage(iqt.ImageQt(img)))

    def save_metadata(self):
        trial_name = 'trial_{0:04d}'.format(self.trial_counter)
        file_list = [f for f in os.listdir(self.data_dir) if f.startswith(trial_name)]
        """ create a document """
        doc = odml.Document()
        """ create dataset section """
        ds = odml.Section('datasets', 'dataset')
        p = odml.Property('files', None)
        ds.append(p)
        for f in file_list:
            p.append('{0:s}/{1:s}'.format(self.data_dir, f))
        doc.append(ds)

        for t in list(self.metadata_tabs.values()):
            m = t.metadata()
            if m.type == 'recording':
                v = odml.Value(self.record_timestamp, dtype='datetime')
                m.append(odml.Property('StartTime', v))
            doc.append(m)

        for cam_name, cam in list(self.cameras.items()):
            s = odml.Section(cam_name,'hardware/camera')
        if not cam.is_raspicam():
            v = odml.Value(frames_per_second, unit="Hz")
            s.append(odml.Property('Framerate', v))
            for p, v in list(cam.get_properties().items()):
                prop = odml.Property(p, v)
                s.append(prop)
            doc.append(s)
        doc.append(self.event_list)
        print(self.event_list)

        from odml.tools.xmlparser import XMLWriter
        writer = XMLWriter(doc)
        writer.write_file('{0}/{1}.xml'.format(self.data_dir, trial_name))

    def update_video(self):
        """ check for programmed stop-time """
        if self.programmed_stop \
                and self.programmed_stop_datetime < datetime.now():
            self.stop_all_recordings()
            self.app.exit()

        is_recording = False
        for cam_name, cam in self.cameras.items():
        # for cam_name, cam in list(self.cameras.items()):
            # grab a frame
            frame, dtime = cam.grab_frame()

            # post-processing
            if self.color:
                frame = frame
            else:
                frame = bgr2grayscale(frame)

            # save frame
            if self.video_recordings is not None:
                self.video_recordings[cam_name].write(frame)
                self.video_recordings[cam_name].write_metadata(dtime)
                is_recording = True

            label = self.videos.tabText(self.videos.currentIndex())

            # display frame
            if label == cam_name and not self.idle_screen:
                if self.color:
                    frame = bgr2rgb(frame)
                img = QtGui.QImage(frame.data, frame.shape[1], frame.shape[0],
                                     frame.shape[1]*3, QtGui.QImage.Format_RGB888)
                self.video_tabs[cam_name].setImage(QtGui.QPixmap(img))

        if is_recording:
            """# display start time """
            timestamp = self.start_time.strftime("%Y-%m-%d  %H:%M:%S")
            time_label = 'start-time: {0:s}   ---  running: {1:s}'.format(timestamp, str(datetime.now() - self.start_time)[:-7])
            self.label_time.setText(time_label)

            """ segmentation for programmed segment length """
            if self.programmed_segmentation and datetime.strptime(self.record_timestamp, '%Y-%m-%d %H:%M:%S') + timedelta(
                seconds=self.programmed_segmentation_datetime.second,
                minutes=self.programmed_segmentation_datetime.minute,
                hours=self.programmed_segmentation_datetime.hour) <= datetime.now():
                self.clicked_stop()
                self.clicked_record()
            #TODO: fix recording_length
            """ check for programmed recording length """
            if self.programmed_recording_length and datetime.strptime(self.record_timestamp, '%Y-%m-%d %H:%M:%S') + timedelta(
                    seconds=self.programmed_recording_length_datetime.second,
                    minutes=self.programmed_recording_length_datetime.minute,
                    hours=self.programmed_recording_length_datetime.hour) <= datetime.now():
                self.stop_all_recordings()
                self.app.exit()

            # self.write_times_file()

    def write_times_file(self):
        for rec in self.video_recordings:
            timefile_name = '{0:s}/trial_{1:04d}_times.dat'.format(self.data_dir, self.trial_counter)
            print(timefile_name)

        with open(timefile_name, 'a') as timefile:
            timefile.write(str(datetime.now() - self.start_time) + "\n")

    # called by metadata-entries in tabs
    # ADAPT to your needs
    @property
    def is_recording(self):
        return self.video_recordings is not None

    def next_tab(self):
        if self.tab.currentIndex() + 1 < self.tab.count():
            self.tab.setCurrentIndex(self.tab.currentIndex() + 1)
        else:
            self.tab.setCurrentIndex(0)

    def prev_tab(self):
        if self.tab.currentIndex() > 0:
            self.tab.setCurrentIndex(self.tab.currentIndex() - 1)
        else:
            self.tab.setCurrentIndex(self.tab.count() - 1)


# #######################################
# WORKER CLASSES


# class ControlCenter(QtCore.QObject):
#     """Put your experiment logic here."""
#
#     def __init__(self, parent=None):
#         QtCore.QObject.__init__(self, parent)
#
#
# class DataCollector(QtCore.QObject):
#     """Collect your data in this class."""
#
#     def __init__(self, parent=None):
#         QtCore.QObject.__init__(self, parent)
#
#
# class Storage(QtCore.QObject):
#     """use this class to store your data periodically."""
#
#     def __init__(self, parent=None):
#         QtCore.QObject.__init__(self, parent)

# #######################################

if __name__ == "__main__":

    args = sys.argv
    to_be_parsed = args[1:]

    # define options parser
    parser = OptionParser()
    parser.add_option("-t", "--template", action="store", type="string", dest="template", default='continuous_recording_template.xml')
    parser.add_option("-k", "--stop_time", action="store", type="string", dest="stop_time", default='')
    parser.add_option("-l", "--recording_length", action="store", type="string", dest="recording_length", default='')
    parser.add_option("-o", "--output_directory", action="store", type="string", dest="output_dir", default='')
    parser.add_option("-s", "--instant_start", action="store_true", dest="instant_start", default=False)
    parser.add_option("-i", "--idle_screen", action="store_true", dest="idle_screen", default=False)
    parser.add_option("-c", "--color", action="store_true", dest="color", default=False)
    parser.add_option("-e", "--segmentation", action="store", dest="segmentation", default='')
    (options, args) = parser.parse_args(args)

    # entering the gui app
    qapp = QtWidgets.QApplication(sys.argv)  # create the main application
    main = Main(qapp, options=options)  # create the mainwindow instance
    main.show()  # show the mainwindow instance
    exit(qapp.exec_())  # start the event-loop: no signals are sent or received without this.
