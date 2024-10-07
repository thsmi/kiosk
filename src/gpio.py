"""
To figure out the line use gpioinfo on the command line.
and to test a pin use gpiomon gpiochip0 18
"""

from abc import ABC
import array
import ctypes
import os
import fcntl
import struct

GPIO_ATTRIBUTE_FLAG = 1
GPIO_ATTRIBUTE_VALUE = 2
GPIO_ATTRIBUTE_DEBOUNCE = 3

GPIO_V2_LINE_FLAG_USED = 1 << 0
GPIO_V2_LINE_FLAG_ACTIVE_LOW = 1 << 1
GPIO_V2_LINE_FLAG_INPUT = 1 << 2
GPIO_V2_LINE_FLAG_OUTPUT = 1 << 3
GPIO_V2_LINE_FLAG_EDGE_RISING = 1 << 4
GPIO_V2_LINE_FLAG_EDGE_FALLING = 1 << 5
GPIO_V2_LINE_FLAG_OPEN_DRAIN = 1 << 6
GPIO_V2_LINE_FLAG_OPEN_SOURCE = 1 << 7
GPIO_V2_LINE_FLAG_BIAS_PULL_UP = 1 << 8
GPIO_V2_LINE_FLAG_BIAS_PULL_DOWN = 1 << 9
GPIO_V2_LINE_FLAG_BIAS_DISABLED = 1 << 10

GPIO_V2_LINES_MAX = 64
GPIO_MAX_NAME_SIZE = 32

GPIO_FLAG_ATTRIBUTE_SIZE = 16
GPIO_VALUE_ATTRIBUTE_SIZE = 16
GPIO_DEBOUNCE_ATTRIBUTE_SIZE = 16
GPIO_V2_LINE_CONFIG_ATTRIBUTE_SIZE = 24
GPIO_V2_LINE_CONFIG_ATTRIBUTES_SIZE = 240
GPIO_V2_LINE_CONFIG_SIZE = 272


GPIO_V2_LINE_NUM_ATTRS_MAX = 8

class GpioException(Exception):
    """
    Thrown in case something goes wrong with gpio.
    """

class GpioV2Attribute(ABC):
    """
    An abstract gpioV2 struct abstraction.
    """

    def __init__(self, identifier):
        self.__id = identifier

    def pack(self) -> bytes:
        """
        Packs the gpio attributes struct.
        """
        data = bytes()
        data += struct.pack("<I", self.__id)
        data += struct.pack("<I", 0)

        return data

class GpioV2FlagAttribute(GpioV2Attribute):
    """
    Configures gpio flags.
    """

    def __init__(self, flags):
        super().__init__(GPIO_ATTRIBUTE_FLAG)
        self.__flags = flags

    def pack(self) -> bytes:
        """
        Packs the flags attribute struct.
        """
        data = super().pack()
        data += struct.pack("<Q", self.__flags)

        if len(data) != GPIO_FLAG_ATTRIBUTE_SIZE:
            raise GpioException(f"Expected 16 bytes but got {len(data)}")

        return data

class GpioV2ValueAttribute(GpioV2Attribute):
    """
    Specifies the Gpio values to set.
    """
    def __init__(self, values):
        super().__init__(GPIO_ATTRIBUTE_VALUE)
        self.__values = values

    def pack(self) -> bytes:
        """
        Packs the value attribute struct.
        """
        data = super().pack()
        data += struct.pack("<Q", self.__values)

        if len(data) != GPIO_VALUE_ATTRIBUTE_SIZE:
            raise GpioException(f"Expected 16 bytes but got {len(data)}")

        return data

class GpioV2DebounceAttribute(GpioV2Attribute):
    """
    Configures the debounce logic.
    """

    def __init__(self, period):
        super().__init__(GPIO_ATTRIBUTE_DEBOUNCE)
        self.__period = period

    def pack(self) -> bytes:
        """
        Packs the debounce attribute struct.
        """
        data = super().pack()
        data += struct.pack("<I", self.__period)
        data += struct.pack("<I", 0)

        if len(data) != GPIO_DEBOUNCE_ATTRIBUTE_SIZE:
            raise GpioException(f"Expected 16 bytes but got {len(data)}")

        return data


class GpioV2LineConfigAttribute():

    def __init__(self, mask, attribute):
        self.__mask = mask
        self.__attribute = attribute

    def pack(self) -> bytes:
        """
        Packs the config attribute struct.
        """
        data = bytes()
        data += self.__attribute.pack()
        data += struct.pack("<Q", self.__mask)

        if len(data) != GPIO_V2_LINE_CONFIG_ATTRIBUTE_SIZE:
            raise GpioException(f"Expected 24 bytes but got {len(data)}")

        return data


class GpioV2LineConfig():

    def __init__(self):
        self.__flags = 0
        self.__attributes = []

    def set_flag(self, flag):
        """
        Sets an gpio flag.
        """
        self.__flags |= flag

    def add_attribute(self, attribute: GpioV2Attribute):
        self.__attributes.append(attribute)

    def add_debounce(self, mask, period):
        self.add_attribute(
            GpioV2LineConfigAttribute(
                mask, GpioV2DebounceAttribute(period)))

    def enable_input(self):
        """
        Switches the pin to input mode.
        """
        self.set_flag(GPIO_V2_LINE_FLAG_INPUT)

    def enable_pull_up(self):
        """
        Enables the internal pull up
        """
        self.set_flag(GPIO_V2_LINE_FLAG_BIAS_PULL_UP)

    def enable_pull_down(self):
        """
        Enables the internal pull down
        """
        self.set_flag(GPIO_V2_LINE_FLAG_BIAS_PULL_DOWN)


    def enable_rising_edge(self):
        """
        Triggers on rising edges
        """
        self.set_flag(GPIO_V2_LINE_FLAG_EDGE_RISING)

    def enable_falling_edge(self):
        """
        Triggers on falling edges
        """
        self.set_flag(GPIO_V2_LINE_FLAG_EDGE_FALLING)

    def pack_attributes(self) -> bytes:
        """
        Packs the attributes into a binary struct. It is zero padded.
        """
        data = bytes()

        for attribute in self.__attributes:
            data += attribute.pack()

        while len(data) != GPIO_V2_LINE_CONFIG_ATTRIBUTES_SIZE:
            data += b"\0"

        if len(data) != GPIO_V2_LINE_CONFIG_ATTRIBUTES_SIZE:
            raise GpioException(f"Expected 240 bytes but got {len(data)}")

        return data

    def pack(self) -> bytes:
        """
        Packs the line config into a binary struct.
        """
        data = bytes()
        data += struct.pack("<Q", self.__flags)
        data += struct.pack("<I", len(self.__attributes))
        data += bytearray([0] * 5 * 4)
        data += self.pack_attributes()

        if len(data) != GPIO_V2_LINE_CONFIG_SIZE:
            raise GpioException(f"Expected 272 bytes but got {len(data)}")

        return data


class GpioV2LineRequest():

    def __init__(self):
        self.__lines = []
        self.__consumer:str = ""
        self.__config = None
        self.__fd: int = 0
        self.__event_buffer_size = 0

    def add_line(self, line):
        """
        Adds a line to be monitored.
        """
        self.__lines.append(line)

    def set_consumer(self, consumer:str):
        """
        Sets the consumer name.
        """
        self.__consumer = consumer

    def set_config(self, config):
        self.__config = config

    def get_fd(self) -> int:
        """
        Returns the file descriptor.
        """
        return self.__fd

    def pack_lines(self) -> bytes:
        """
        Packs the lines config struct used by the line request.
        """
        data = bytes()

        for line in self.__lines:
            data += struct.pack("<I", line)

        while len(data) != GPIO_V2_LINES_MAX*4:
            data += b"\0"

        if len(data) != 256:
            raise GpioException(f"Expected 272 bytes but got {len(data)}")

        return data

    def pack_consumer(self) -> bytes:
        """
        Packs the consumer name into a struct used by the line request.
        """

        data = bytes()
        data += self.__consumer.encode("utf-8")

        while len(data) != GPIO_MAX_NAME_SIZE:
            data += b"\0"

        return data

    def pack_config(self) -> bytes:
        """
        Packs the line config structs used by the line request.
        """

        if self.__config:
            return self.__config.pack()

        data = bytes()
        for i in range(272):
            data += i

        return data

    def pack(self) -> bytes:
        """
        Packs the line request struct.
        """
        data = bytes()
        data += self.pack_lines()
        data += self.pack_consumer()
        data += self.pack_config()
        data += struct.pack("<I", len(self.__lines))
        data += struct.pack("<I", self.__event_buffer_size)
        data += bytearray([0] * 5 * 4)
        data += struct.pack("<i", self.__fd)

        if len(data) != 592:
            raise GpioException(f"Expected 592 bytes but got {len(data)}")

        return data

    def unpack(self, data):
        """
        Unpacks the response the the line request, which is typically a file handle.
        """
        if len(data) != 592:
            raise GpioException(f"Expected 592 bytes but got {len(data)}")

        # Convert the bytes to an integer using struct.unpack
        self.__fd = struct.unpack('<I', data[-4:])[0]


class GpioV2LineValues():

    def __init__(self):
        self.__bits = 0
        self.__mask = 0

    def set_mask(self, mask):
        """
        Sets the mask which specifies which values should be monitored.
        """
        self.__mask = mask

    def is_high(self, bit:int) -> bool:
        """
        Checks if the given bit is active.
        """
        return (self.__bits & (1 << bit)) != 0

    def pack(self) -> bytearray:
        """
        Packs the line value structs.
        """
        data = bytearray()
        data += struct.pack("<Q", self.__bits)
        data += struct.pack("<Q", self.__mask)
        return data

    def unpack(self, data):
        if len(data) != 16:
            raise GpioException(f"Expected 16 bytes but got {len(data)}")

        self.__bits = struct.unpack('<Q', data[:8])[0]


class GpioDevice:
    def __init__(self, device):
        self.__device = device
        self.__fd = -1

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self.close()
        return False

    def open(self):
        """
        Opens the gpio device.
        """
        self.__fd = os.open(self.__device, os.O_RDWR)
        if self.__fd == -1:
            raise GpioException(
                f"Failed to open {self.__device}, {os.strerror(ctypes.get_errno())}")

    def close(self):
        """
        Closes the gpio device.
        """
        if self.__fd != -1:
            os.close(self.__fd)

        self.__fd = -1

    def get_lines(self,name, lines, config):
        """
        Gets the lines from the gpio device.
        """

        req = GpioV2LineRequest()

        for line in lines:
            req.add_line(line)

        req.set_config(config)
        req.set_consumer(name)

        data = array.array("B",req.pack())
        # GPIO_GET_LIN_CTL
        fcntl.ioctl(self.__fd, 3260068871, data, 1)
        req.unpack(data)

        return GpioLine(req.get_fd(), lines)

class GpioLine():
    """
    Abstracts a gpio line configuration.
    """
    def __init__(self, fd, lines):
        self.__fd = fd
        self.__lines = lines

    def get_fd(self):
        """
        Returns the file descriptor needed to read this gpio line.
        """
        return self.__fd

    def get_active(self):
        """
        Checks if the gpio line is active.
        """
        lv = GpioV2LineValues()

        mask = 0
        for i in range(len(self.__lines)):
            mask |= (1 << i)

        lv.set_mask(mask)

        data = array.array("B",lv.pack())
        # GPIO_V2_LINE_GET_VALUES_IOCTL
        fcntl.ioctl(self.__fd, 3222320142, data, 1)
        lv.unpack(data)

        res = {}

        #logging.getLogger('flask.app').error(str(active))

        for line in range(len(self.__lines)):
            # we need to invert we have pull ups
            if  lv.is_high(line):
                res[self.__lines[line]] = True
            else:
                res[self.__lines[line]] = False

        return res
