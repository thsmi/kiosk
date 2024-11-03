"""
Controls what is displayed on the screen,
in explicit the the X11 session as well as the browser.
"""

from __future__ import annotations

import shutil
import subprocess
import pathlib
import re
from typing import List

from src.sed import SingleLineEditor

CONFIG_BROWSER = pathlib.Path("/etc/kiosk/browser.conf")
CONFIG_XINITRC_SCREENS = pathlib.Path("/etc/kiosk/screens.d")
CONFIG_WM_SERVICE_FILE = "kiosk-windowmanager.service"

CMD_SET_SCREEN = "xrandr --output"

CMD_GET_SCREENS = "xrandr --display :0 --query --verbose"
REGEX_GET_SCREEN_PROPERTIES =  r"^(?P<name>\S+) (connected|disconnected) \S+( \S+)?( (\d+)x(\d+)\S+ \S+ (\S+))?"

CMD_DISPLAY = "DISPLAY=:0"
CMD_DISPLAY_STATUS = "xset -q"
CMD_DISPLAY_FORCE_ON = "xset dpms force on"
CMD_DISPLAY_FORCE_OFF = "xset dpms force off"
CMD_DISPLAY_SCREENSAVER_OFF = "xset s off"
CMD_DISPLAY_SCREENSAVER_BLANK_OFF = "xset s noblank"
CMD_DISPLAY_POWER_MANAGEMENT_OFF = "xset -dpms"

class DisplayException(Exception):
    """
    Throw in case something failed during screen configuration.
    """

class Screen():
    """
    Represents a physical screen or monitor which is associated to a display.
    """

    def __init__(self, name):
        if not re.match("^[A-Za-z0-9_-]*$", name):
            raise DisplayException(f"Invalid screen name {name}")

        self.__name = name
        self.__status = "unknown"
        self.__primary = False
        self.__x_resolution = 0
        self.__y_resolution = 0
        self.__orientation = "normal"

    def load(self, xrandr_data:str=None) -> Screen:
        """
        Loads the current configuration.
        """

        pattern =  (f"^{self.__name}"
            " (?P<status>disconnected|connected)"
            "( (?P<primary>primary))?"
            "( (?P<x_resolution>\\d+)x(?P<y_resolution>\\d+)\\S+ \\S+ (?P<orientation>\\S+))?")

        if not xrandr_data:
            xrandr_data = subprocess.run(
                CMD_GET_SCREENS, shell=True,
                capture_output=True, text=True, check=True).stdout

        match = re.search(pattern, xrandr_data.strip(), re.MULTILINE)

        if not match:
            raise DisplayException(f"No screen {self.__name} found")

        self.__status = match.group('status')
        self.__primary = match.group('primary')
        self.__x_resolution = match.group('x_resolution')
        self.__y_resolution = match.group('y_resolution')
        self.__orientation = match.group("orientation")

        if self.__orientation is None:
            self.__orientation = "normal"

        return self

    def get_name(self) -> str:
        """
        Returns the screens name.
        """
        return self.__name

    def get_status(self) -> str:
        """
        Returns the screens status.
        """
        return self.__status


    def is_connected(self) -> bool:
        """
        Checks if the screen is connected or not.
        """
        if str(self.__status).lower() == "connected":
            return True

        return False


    def get_x_resolution(self) -> int:
        """
        Gets the x resolution
        """
        if self.__x_resolution is None:
            return 0

        return int(self.__x_resolution)

    def get_y_resolution(self) -> int:
        """
        Gets the y resolution
        """
        if self.__y_resolution is None:
            return 0

        return int(self.__y_resolution)

    def is_primary(self) -> bool:
        """
        Checks if the current screen is the primary screen.
        It reads the information from the config file and in
        case this fails it returns the current information from
        xrandr.
        """

        sed = SingleLineEditor(CONFIG_XINITRC_SCREENS / self.__name)

        line = sed.get_line(f"{CMD_SET_SCREEN} {self.__name}")
        if not line:
            return self.__primary

        match = re.search(r"--primary", line)
        if match:
            return False

        return True

    def get_orientation(self) -> str:
        """
        Returns the screens orientation. It reads it from the file and 
        in case this fails it falls back to the information from xrandr.
        """

        sed = SingleLineEditor(CONFIG_XINITRC_SCREENS / self.__name)

        line = sed.get_line(f"{CMD_SET_SCREEN} {self.__name}")
        if not line:
            return self.__orientation

        match = re.search(r"--rotate\s+(?P<orientation>\S+)", line)
        if not match:
            return self.__orientation

        return match.group("orientation")

    def is_enabled(self):
        """
        Checks if the screens output is enabled.
        """
        sed = SingleLineEditor(CONFIG_XINITRC_SCREENS / self.__name)

        line = sed.get_line(f"{CMD_SET_SCREEN} {self.__name}")
        if not line:
            return self.__primary

        match = re.search(r"--off", line)
        if not match:
            return True

        return False

    def disable(self):
        """
        Disables the screen.
        """

        with (CONFIG_XINITRC_SCREENS / self.__name).open("w+") as f:
            f.write("#!/bin/sh\n")
            f.write(CMD_SET_SCREEN + f" {self.__name} --off\n")

        (CONFIG_XINITRC_SCREENS / self.__name).chmod(0o775)

    def enable(self, orientation:str  = None):
        """
        Enables the screen.
        """

        if orientation is None:
            orientation = self.get_orientation()

        with (CONFIG_XINITRC_SCREENS / self.__name).open("w+") as f:
            f.write("#!/bin/sh\n")
            f.write(CMD_SET_SCREEN + f" {self.__name} --rotate {orientation} --primary\n")

        (CONFIG_XINITRC_SCREENS / self.__name).chmod(0o775)

class Browser:
    """
    Configures the Chromium browser.
    """

    def __init__(self):
        self.__browser_config = SingleLineEditor(CONFIG_BROWSER)

    def get_url(self) -> str:
        """
        Gets the currently set homepage.
        """
        return self.__browser_config.get_line("KIOSK_HOME=")[11:].strip()

    def set_url(self, url:str) -> str:
        """
        Sets the kiosk homepage.
        """
        self.__browser_config.update_line(
            "KIOSK_HOME=", f'KIOSK_HOME={url}')

    def get_scale(self) -> float:
        """
        Gets the current scale factor.
        """
        return float(self.__browser_config.get_line("KIOSK_SCALE_FACTOR=")[19:].strip())

    def set_scale_factor(self, scale :str):
        """
        Sets the scale factor for high density displays.
        """
        self.__browser_config.update_line(
            "KIOSK_SCALE_FACTOR=", f'KIOSK_SCALE_FACTOR={scale}')

    def reload(self):
        """
        Restarts the browser.
        """
        subprocess.run("systemctl restart kiosk-browser.service", shell=True, check=True)

class Display:
    """
    Class to control the window manager and the browser.

    A display is associated with zero or more screens.
    """

    def __init__(self):
        pass

    def get_screenshot(self, scale: int = None, picture_format: str = None) -> bytes:
        """
        Takes a screenshot from the current screen and returns it as png.
        """

        if not picture_format:
            picture_format = "png"

        if not scale:
            scale = 10

        xwd_command = ["xwd", "-silent", "-root", "-display",":0"]
        convert_command = ["convert", "xwd:-", "-resize", f"{scale}%", f"{picture_format}:-"]

        # Run xwd command and capture its output
        xwd_process = subprocess.run(
            xwd_command, stdout=subprocess.PIPE, check=True)

        # Run convert command with xwd output as input
        convert_process = subprocess.run(
            convert_command, input=xwd_process.stdout, stdout=subprocess.PIPE, check=True)

        return convert_process.stdout

    def on(self):
        """
        Turns the display on and ensures the screensaver is disabled.
        """

        subprocess.run(
            ["/bin/bash", "-c", f"{CMD_DISPLAY} {CMD_DISPLAY_FORCE_ON}"], check=True)
        subprocess.run(
            ["/bin/bash", "-c", f"{CMD_DISPLAY} {CMD_DISPLAY_SCREENSAVER_OFF}"], check=True)
        subprocess.run(
            ["/bin/bash", "-c", f"{CMD_DISPLAY} {CMD_DISPLAY_POWER_MANAGEMENT_OFF}"], check=True)
        subprocess.run(
            ["/bin/bash", "-c", f"{CMD_DISPLAY} {CMD_DISPLAY_SCREENSAVER_BLANK_OFF}"], check=True)

    def off(self):
        """
        Turns the display off.
        """

        subprocess.run(
            ["/bin/bash", "-c", f"{CMD_DISPLAY} {CMD_DISPLAY_FORCE_OFF}"], check=True)

    def is_off(self):
        """
        Checks if the display is off.
        """

        result = subprocess.run(
            ["/bin/bash", "-c", f"{CMD_DISPLAY} {CMD_DISPLAY_STATUS}"],
            stdout=subprocess.PIPE, text=True, check=True)

        for line in result.stdout.splitlines():
            if line.strip() == "Monitor is Off":
                return True

        return False

    def get_screens(self) -> List[Screen]:
        """
        Returns a list of all screens attached to the system.
        """

        xrandr_data = subprocess.run(
            CMD_GET_SCREENS, shell=True,
            capture_output=True, text=True, check=False).stdout.strip()

        matches = re.finditer(REGEX_GET_SCREEN_PROPERTIES, xrandr_data, re.MULTILINE)

        result = []

        for _, match in enumerate(matches, start=1):
            result.append(Screen(match.group('name')).load(xrandr_data))

        return result

    def get_screen(self, name) -> Screen:
        """
        Gets a screen by his unique name.
        """

        return Screen(name).load()

    def set_screen(self, name:str, orientation:str):
        """
        Enables the given display and sets the orientation.
        """

        # Clear all existing configs
        shutil.rmtree(CONFIG_XINITRC_SCREENS)
        CONFIG_XINITRC_SCREENS.mkdir(exist_ok=True)

        # And create new ones.
        for screen in self.get_screens():

            if screen.get_name() != name:
                screen.disable()
                continue

            screen.enable(orientation)

        self.reload()

    def reload(self):
        """
        Restarts the window manager.
        """

        subprocess.run(f"systemctl restart {CONFIG_WM_SERVICE_FILE}", shell=True, check=True)
