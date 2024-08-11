"""
Implements a logic for a motion sensor.
"""
import logging
import threading
from src.gpio import GpioMonitor
from src.screen import Screen

class MotionSensor:
    """
    Controls a screen with a motion sensor.
    """

    def __init__(self, screen: Screen, delay:int):
        self.__gpio_monitor = GpioMonitor("/dev/gpiochip0", [18])

        self.__screen = screen
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
        return self.__gpio_monitor.is_enabled()

    def run(self):
        """
        Used by the thread to run the blocking call to the gpio monitor.
        """
        self.__gpio_monitor.enable()

    def enable(self):
        """
        Starts monitoring the motion sensor.
        """

        # Already running
        if self.__worker:
            return

        self.__gpio_monitor.set_trigger(self.on_trigger)
        self.__worker = threading.Thread(target=self.run)
        self.__worker.start()

    def disable(self):
        """
        Stops monitoring the motion sensor.
        """

        self._cancel_timeout()

        if self.__worker:
            self.__gpio_monitor.disable()
            self.__worker = None

    def turn_on(self):
        """
        Cancels any turn off timers and turns the screen on.
        """
        logging.getLogger('flask.app').error("XXXXX Turning Screen On")
        self._cancel_timeout()

        if self.__screen.is_off():
            self.__screen.on()

    def turn_off(self):
        """
        Turns off the screen.        
        """

        logging.getLogger('flask.app').error("XXXXX Turning Screen On")

        self._cancel_timeout()
        self.__screen.off()

    def on_trigger(self, active):
        """
        When the sensor falls to low it has a three second time span where it 
        needs to regenerate and won't measure anything
        """

        logging.getLogger('flask.app').error(str(active))

        if 18 not in active:
            return

        if active[18] is True:
            self.turn_on()
            return

        # The sensor goes low for three seconds between
        # consultive samples. Means any off signal need to be low
        # for way more than three seconds.
        # Otherwise we'll resonate between the on and off state.
        self._start_timeout(self.__delay, self.turn_off)
