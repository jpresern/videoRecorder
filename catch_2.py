#!/usr/bin/env python3
import urllib.request
import cv2, platform
#import numpy as np


# import cv2
# cam = "http://192.168.1.6:80/html/cam_pic_new.php?"
# cam = "http://192.168.1.6:8160"
cam = "rtsp://192.168.1.6:8554/"
stream = urllib.request.urlopen(cam)
cap = cv2.VideoCapture(stream)
fwidth = cap.get(3)
fheight = cap.get(4)


fourcc = cv2.VideoWriter_fourcc(*'XVID')

out = cv2.VideoWriter('output.avi',fourcc, 20.0, (fwidth,fheight))



while True:
  ret, frame = cap.read()
  cv2.imshow('Video', frame)

  if cv2.waitKey(1) == 27:
    exit(0)


# import cv2
# # cap = cv2.VideoCapture('http://192.168.1.6:8082/frame.mjpg')
# cap = cv2.VideoCapture('http://192.168.1.6:8000')
#
# while True:
#     ret, frame = cap.read()
#     # cv2.imshow('Video', frame)
#
#     if cv2.waitKey(1) == 27:
#         exit(0)