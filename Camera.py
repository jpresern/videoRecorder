import warnings
from datetime import datetime
import cv2
import numpy as np
from CamController import CamController

__author__ = 'fabee, jpresern'


def bgr2rgb(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def brg2hsv(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)


def bgr2grayscale(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    frame = np.expand_dims(frame, 2)
    frame = np.repeat(frame, 3, 2)
    return frame


class Camera:
    def __init__(self, device_no=0, post_processor=None):
        """
        Initializes a new camera

        :param post_processor: function that is applies to the frame after grabbing
        """
        self.capture = None
        self.device_no = device_no
        self.post_processor = post_processor
        if post_processor is None:
            self.post_processor = lambda x, y: (x, y)

        self.open()


    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def open(self):
        # capture = cv2.VideoCapture(self.device_no)
        # self.capture = capture
        self.capture = cv2.VideoCapture(self.device_no)
        ### define the control section
        # self.cam_controller = CamController(self.device_no)

    def is_working(self):
        return self.capture.isOpened()

    def get_properties(self):
        """
        :returns: the properties (cv2.CAP_PROP_*) from the camera
        :rtype: dict
        """
        if self.capture is not None:

            properties = [e for e in dir(cv2) if "CV_CAP_PROP" in e]
            ret = {}
            for e in properties:

                ret[e[12:].lower()] = self.capture.get(getattr(cv2, e))
            return ret
        else:
            warnings.warn("Camera needs to be opened first!")
            return None

    def get_resolution(self):
        if self.capture is not None:
            return int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)), \
                   int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        else:
            raise ValueError("Camera is not opened or not functional! Capture is None")

    def grab_frame(self):
        dtime = datetime.now()
        flag, frame = self.capture.read()

        if not flag:
            warnings.warn("Couldn't grab frame from camera!")
            return None
        else:
            return self.post_processor(frame, dtime)
        # return

    def is_raspicam(self):
        return False

    def close(self):
        pass

