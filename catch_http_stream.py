#!/usr/bin/env python3

import cv2, platform
import numpy as np
import urllib.request
# import Tkinter
import os
# from PIL import Image, ImageTk
# import threading


def cvloop(cam, out):
    # stream=open('output.mjpg','rb')
    stream = urllib.request.urlopen(cam)
    bites = bytes()
    count = 0


    while True:
        bites += stream.read(8192)
        # bites += stream.read()
        a = bites.find(b'\xff\xd8')
        b = bites.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bites[a:b+2]
            bites = bites[b+2:]
            frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow('slika',frame)
            out.write(frame)
            count += 1
            print(count)
            if cv2.waitKey(1) & 0xFF == ord('q'):
            # if cv2.waitKey(1) == 27:
                exit(0)



if __name__ == "__main__":

    """ prepare URL """
    cam = "http://192.168.1.6:80/html/cam_pic_new.php?"

    """ open stream and check frame size """
    # stream=open('output.mjpg','rb')
    stream = urllib.request.urlopen(cam)
    bites = bytes()
    count = 0

    """ detect frame size """
    bites += stream.read(8192)
    # bites += stream.read()
    a = bites.find(b'\xff\xd8')
    b = bites.find(b'\xff\xd9')
    if a != -1 and b != -1:
        jpg = bites[a:b + 2]
        print(len(jpg))
        bites = bites[b + 2:]
        i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

    """ prepare cv2 writer """
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter('output.mkv', fourcc, 25, (i.shape[1], i.shape[0]))
    # fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    # out = cv2.VideoWriter('output.avi', fourcc, 25, (i.shape[1], i.shape[0]))
    # fourcc = cv2.VideoWriter_fourcc('A','V','C','1')
    # out = cv2.VideoWriter('output.mp4', fourcc, 25, (i.shape[1], i.shape[0]))
    # fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', 'V')
    # out = cv2.VideoWriter('output.avi', fourcc, 25, (i.shape[1], i.shape[0]))
    # fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', 'V')
    # out = cv2.VideoWriter('output.m', fourcc, 25, (i.shape[1], i.shape[0]))
    # fourcc = cv2.VideoWriter_fourcc('H', '2', '6', '4')
    # out = cv2.VideoWriter('output.mp4', fourcc, 25, (i.shape[1], i.shape[0]))
    # fourcc = cv2.VideoWriter_fourcc('i', 'Y', 'U', 'V')
    # out = cv2.VideoWriter('output.avi', fourcc, 25, (i.shape[1], i.shape[0]))

    """FourCC code they specify for the H264 standard is actually 'X','2','6','4', so if 'H','2','6','4' doesn't work, replace H with X.

    Another small note. If you are using Mac OS, then what you need to use is 'A','V','C','1' or 'M','P','4','V'. From experience, 'H','2','6','4'or 'X','2','6','4'when trying to specify the FourCC code doesn't seem to work."""

    """
    int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    """


    """ main recording loop """
    cvloop(cam, out)

    """ release everything """
    out.release()
    cv2.destroyAllWindows()

