import picamera
import pickle


class RasPiVideoRecording(object):
    def __init__(self, filename, filename_metadata, codec, raspicam):
        self.cam = raspicam
        self.filename = filename
        self.filename_metadata = filename_metadata
        self.cam.camera.start_recording(filename, format=codec)

    def write(self, x):
        pass

    def write_metadata(self, current_datetime):
        with open(self.filename_metadata, 'w') as f:
            f.write(str(current_datetime).split(".")[0])
            f.flush()

    def stop(self):
        self.cam.camera.stop_recording()