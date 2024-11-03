"""
Implements a logic for a motion sensor.
"""
from enum import Enum
import logging
import os
import threading
from src.gpio import GpioDevice, GpioV2LineConfig
from src.display import Display

class MotionSensorState(Enum):
    """
    Small state machine to track the gpio monitors states.
    """
    IDLE = 1
    RUNNING = 2
    STOPPING = 3

class MotionSensor:
    """
    Controls a screen with a motion sensor.
    """

    def __init__(self, display: Display, delay:int):
        self.__device = "/dev/gpiochip0"
        self.__line = 18
        self.__state = MotionSensorState.IDLE

        self.__display = display
        self.__timer = None
        self.__worker = None
        self.__delay = delay

    def _start_timeout(self, delay:float, callback):
        """
        Starts a deferred function call.
        The delay as float.
        """
        self.__timer = threading.Timer(float(delay), callback)
        self.__timer.start()

    def _cancel_timeout(self):
        """
        Cancels a deferred function call in case it is active.
        """
        if not self.__timer:
            return

        self.__timer.cancel()
        self.__timer = None

    def get_delay(self) -> int:
        """
        Gets the currently set delay
        """
        return self.__delay

    def set_delay(self, delay:int):
        """
        Sets the currently set delay
        """
        self.__delay = delay

    def is_enabled(self) -> bool:
        """
        Checks if the motion sensor is enabled.
        """
        return self.__state != MotionSensorState.IDLE

    def run(self):
        """
        Used by the thread to run the blocking call to the gpio monitor.
        """
        if self.__state is not MotionSensorState.IDLE:
            self.__state = MotionSensorState.RUNNING
            return

        self.__state = MotionSensorState.RUNNING

        try:
            with GpioDevice(self.__device) as dev:
                config = GpioV2LineConfig()
                config.enable_input()
                config.enable_pull_down()
                config.enable_rising_edge()
                config.enable_falling_edge()

                lines = dev.get_lines("kiosk", [self.__line], config)

                while self.__state is MotionSensorState.RUNNING:
                    os.read(lines.get_fd(), 48)
                    active = lines.get_active()

                    if active[self.__line] is True:
                        self.turn_on()
                        continue

                    # The sensor goes low for three seconds between
                    # consultive samples. Means any off signal need to be low
                    # for way more than three seconds.
                    # Otherwise we'll resonate between the on and off state.
                    self._start_timeout(self.__delay, self.turn_off)
        finally:
            self.__state = MotionSensorState.IDLE

    def enable(self):
        """
        Starts monitoring the motion sensor.
        """

        if self.__state is MotionSensorState.RUNNING:
            return

        # In case it is stopping the just cancel the stop request.
        if self.__state is MotionSensorState.STOPPING:
            self.__state = MotionSensorState.RUNNING
            return

        self.__worker = threading.Thread(target=self.run)
        self.__worker.start()

    def disable(self):
        """
        Stops monitoring the motion sensor.
        """

        self._cancel_timeout()
        self.__state = MotionSensorState.STOPPING

    def turn_on(self):
        """
        Cancels any turn off timers and turns the screen on.
        """
        logging.getLogger('flask.app').debug("Turning Screen On")
        self._cancel_timeout()

        if self.__display.is_off():
            self.__display.on()

    def turn_off(self):
        """
        Turns off the screen.        
        """

        logging.getLogger('flask.app').debug("Turning Screen On")

        self._cancel_timeout()
        self.__display.off()
