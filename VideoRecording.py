import cv2

__author__ = 'Fabian Sinz, Janez Presern'


class VideoRecording:

    def __init__(self, filename, filename_metadata, resolution, fps, codec, color=True):
        self.filename = filename
        self.filename_metadata = filename_metadata
        self.writer = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*codec), int(fps), resolution, color)

    def write(self, frame):
        self.writer.write(frame)

    def write_metadata(self, current_datetime):
        with open(self.filename_metadata, 'w') as f:
            f.write(str(current_datetime).split(".")[0])
            f.flush()

    def stop(self):
        pass
