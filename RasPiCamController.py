class Attribute(object):
    def __init__(self, name, handle):
        self._name = name
        self._handle = handle

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def handle(self):
        return self._handle
    @handle.setter
    def handle(self, function):
        self._handle = function

class AttributeNumber(Attribute):
    def __init__(self, name, handle, min, max, default):
        super(AttributeNumber, self).__init__(name, handle)
        self._min = min
        self._max = max
        self._default = default
        self._current = default

    @property
    def min(self):
        return self._min
    @min.setter
    def min(self, value):
        self._min = value

    @property
    def max(self):
        return self._max
    @max.setter
    def max(self, value):
        self._max = value

    @property
    def default(self):
        return self._default
    @default.setter
    def default(self, value):
        self._default = value

    @property
    def current(self):
        return self._current
    @current.setter
    def current(self, value):
        self._current = value

class AttributeOptions(Attribute):
    def __init__(self, name, handle, options, default_index):
        super(AttributeOptions,self).__init__(name, handle)
        self._options = options
        self._default_index = default_index
        self._current = options[default_index]

    @property
    def options(self):
        return self._options
    @options.setter
    def options(self, option_list):
        self._options = option_list

    @property
    def default_index(self):
        return self._default_index
    @default_index.setter
    def default_index(self, value):
        self._default_index = value

    @property
    def current(self):
        return self._current
    @current.setter
    def current(self, value):
        self._current = value

class RasPiCamController(object):
    def __init__(self, raspicam):
        self.cam = raspicam

        self.brightness_min = 0
        self.brightness_max = 100
        self.brightness_default = 50
        self.brightness = AttributeNumber('brightness', self.set_brightness, self.brightness_min, self.brightness_max, self.brightness_default)

        self.contrast_min = -100
        self.contrast_max = 100
        self.contrast_default = 0
        self.contrast = AttributeNumber('contrast', self.set_contrast, self.contrast_min, self.contrast_max, self.contrast_default)

        self.exposure_compensation_min = -25
        self.exposure_compensation_max = 25
        self.exposure_compensation_default = 0
        self.exposure_compensation = AttributeNumber('exposure compensation', self.set_exposure_compensation, self.exposure_compensation_min, self.exposure_compensation_max, self.exposure_compensation_default)

        self.exposure_mode_options = ['off', 'auto', 'night',  'nightpreview', 'backlight', 'spotlight',
                                      'sports', 'snow', 'beach', 'verylong', 'fixedfps', 'antishake', 'fireworks']
        self.exposure_mode_default = 1
        self.exposure_mode = AttributeOptions('exposure mode', self.set_exposure_mode, self.exposure_mode_options, self.exposure_mode_default)

        self.iso_options = [100, 200, 400, 800, 1600]
        self.iso_default = 0
        self.iso = AttributeOptions('iso', self.set_iso, self.iso_options, self.iso_default)

        self.meter_mode_options = ['average', 'spot', 'backlit', 'matrix']
        self.meter_mode_default = 0
        self.meter_mode = AttributeOptions('meter mode', self.set_meter_mode, self.meter_mode_options, self.meter_mode_default)

        self.attributes = [self.brightness, self.contrast, self.iso, self.exposure_compensation, self.exposure_mode, self.meter_mode]

    def set_brightness(self, value):
        if not self.brightness_min <= value <= self.brightness_max:
            print ("brightness value must be within {0:d} ... {1:d}. Default: {2:d}".format(self.brightness_min, self.brightness_max, self.brightness_default))
            return False
            self.cam.brightness = int(value)
            return True

    def set_contrast(self, value):
        if not self.contrast_min <= value <= self.contrast_max:
            print ("contrast value must be within {0:d} ... {1:d}. Default: {2:d}".format(self.contrast_min, self.contrast_max, self.contrast_default))
            return False
            self.cam.contrast = int(value)
            return True

    def set_exposure_compensation(self, value):
        """
    Sets the exposure compensation to given value. Higher values result in brighter images.
    """
        if not self.exposure_compensation_min <= value <= self.exposure_compensation_max:
            print ("exposure compensation must be within {0:d} ... {1:d}. Default: {2:d}".format(self.exposure_compensation_min, self.exposure_compensation_max, self.exposure_compensation_default))
            return False
            self.cam.exposure_compensation = int(value)
            return True

    def set_exposure_mode(self, mode):
        if mode not in self.exposure_mode_options:
            print ("Mode must be one of: " + str(self.exposure_mode_options) + "\nDefault: auto")
            return False
            self.cam.exposure_mode = str(mode)
            return True

    def set_iso(self, value):
        if int(value) not in self.iso_options:
            print ("value must be one of " + str(self.iso_options) + " Default: 100")
            return False
            self.cam.iso = int(value)
            return True

    def set_meter_mode(self, mode):
        """
    Sets the mode to determine the camera uses to determine exposure time. Default: average
    """
        if mode not in self.meter_mode_options:
            print ("Mode must be one of: " + str(self.meter_mode_options) + "\nDefault: average")
            return False
            self.cam.meter_mode = str(mode)
            return True
