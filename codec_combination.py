#!/usr/bin/env python3

import numpy as np
import cv2
# import VideoRecording

__author__ = 'Janez Presern'

codecs = ['mp4v', 'MJPG', 'XVID', 'DIVX', 'h264', 'x264', 'H264', 'X264', 'h265', 'x265', 'H265', 'X265', 'AVC1',
          'MP4V', 'IYUV', 'PIM1', 'FLV1', 'MSVC']
file_types = ['mp4', 'avi', 'mov', 'mkv', 'flv', 'ogg', 'mp4', 'mp4v', 'avc1', 'mpg', 'wmv']


for codec in codecs:
    for file_type in file_types:

        cap = cv2.VideoCapture(0)

        W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
        H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)

        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter('./codec_test/output' + '_' + codec + '.' + file_type, fourcc, 20.0, (W,H))

        counter = 0
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret==True:
                frame = cv2.flip(frame, 0)

                out.write(frame)

                # cv2.imshow('frame', frame)
                counter += 1
                if counter == 30:
                    break
            else:
                break
        print('Success: ' + codec + ' + ' + file_type)

        cap.release()

        # cv2.destroyAllWindows()