import numpy as np
# from PIL import Image as image
# from PIL import ImageQt as iqt
try:
    from PyQt5 import QtGui, QtCore, QtWidgets
except:
    print('Unfortunately, your system misses the PyQt5 packages.')
    quit()

__author__ = 'Fabian Sinz'


class VideoCanvas(QtWidgets.QLabel):
    """This class creates the video-canvas-widget in the mainwindow by subclassing the QLabel-Widget"""
    # TODO fix fullscreen scaling of input-image
    def __init__(self, parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        self.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)

        self.canvas_w = 640
        self.canvas_h = 480

        # img = image.fromarray(np.zeros((self.canvas_h, self.canvas_w))).convert('RGB')
        # img = image.fromarray(np.zeros((self.canvas_h, self.canvas_w)))
        # self.setImage(QtGui.QPixmap.fromImage(iqt.ImageQt(img)))

        img = np.zeros((self.canvas_h, self.canvas_w, 3))
        img = QtGui.QImage(img.data, img.shape[1], img.shape[0],
                             img.shape[1] * 3, QtGui.QImage.Format_RGB888)
        self.setImage(QtGui.QPixmap(QtGui.QImage(img)))
        # self.video_tabs[cam_name].setImage(QtGui.QPixmap.fromImage(iqt.ImageQt(image.fromarray(frame))))

    def resizeEvent(self, QResizeEvent):
        """ override in-built Qt function """
        self.resizeImage()

    def setImage(self, pixmap):
        self.setPixmap(pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio))

    def resizeImage(self):
        self.setPixmap(self.pixmap().scaled(self.size(), QtCore.Qt.KeepAspectRatio))
