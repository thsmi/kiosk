"""
Controls what is displayed on the screen,
in explicit the the X11 session as well as the browser.
"""
import subprocess
import pathlib
import re

CONFIG_BROWSER = pathlib.Path("/etc/kiosk/browser.conf")
CONFIG_XINITRC = pathlib.Path("/etc/kiosk/xinitrc")
CONFIG_WM_SERVICE_FILE = "kiosk-windowmanager.service"

SCREEN_1 = "HDMI-1"
SCREEN_2 = "HDMI-2"

CMD_SCREEN_1_ON = f"xrandr --output {SCREEN_1}"
CMD_SCREEN_2_OFF = f"xrandr --output {SCREEN_2} --off"
REGEX_XRANDR =  r"^HDMI-1 connected primary (?P<x_resolution>\d+)x(?P<y_resolution>\d+)\S+ \S+ (?P<orientation>\S+)"

CMD_SCREEN_QUERY = "xrandr --display :0 --query --verbose"

CMD_DISPLAY = "DISPLAY=:0"
CMD_DISPLAY_STATUS = "xset -q"
CMD_DISPLAY_FORCE_ON = "xset dpms force on"
CMD_DISPLAY_FORCE_OFF = "xset dpms force off"
CMD_DISPLAY_SCREENSAVER_OFF = "xset s off"
CMD_DISPLAY_SCREENSAVER_BLANK_OFF = "xset s noblank"
CMD_DISPLAY_POWER_MANAGEMENT_OFF = "xset -dpms"

class Screen:
    """
    Class to control the window manager and the browser.
    """

    def __init__(self) -> None:
        pass

    def __get_line(self, filename:pathlib.Path, search:str):
        """
        Parses the file and returns the line starting with the search string.
        """

        with filename.open('r', encoding="utf-8") as file:
            for line in file:
                if not line.startswith(search):
                    continue

                return line

    def __update_line(self, filename:pathlib.Path, search:str, replacement:str):
        """
        Parses the file and updates the line starting with the search string.
        """
        with filename.open('r', encoding="utf-8") as file:
            lines = file.readlines()

        # Modify the line that starts with KIOSK_HOME=
        with filename.open('w', encoding="utf-8") as file:
            for line in lines:
                if line.startswith(search):
                    file.write(replacement+"\n")
                    continue

                file.write(line)

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

    def get_url(self) -> str:
        """
        Gets the currently set homepage.
        """
        return self.__get_line(CONFIG_BROWSER, "KIOSK_HOME=")[11:].strip()

    def set_url(self, url:str) -> str:
        """
        Sets the kiosk homepage.
        """
        self.__update_line(
            CONFIG_BROWSER ,
            "KIOSK_HOME=",
            f'KIOSK_HOME={url}')

    def get_scale(self) -> float:
        """
        Gets the current scale factor.
        """
        return float(self.__get_line(CONFIG_BROWSER, "KIOSK_SCALE_FACTOR=")[19:].strip())

    def set_scale_factor(self, scale :str):
        """
        Sets the scale factor for high density displays.
        """
        self.__update_line(
            CONFIG_BROWSER,
            "KIOSK_SCALE_FACTOR=",
            f'KIOSK_SCALE_FACTOR={scale}')

    def get_orientation(self):
        """
        Gets the screen orientation and dimensions or returns null if no screen was found.
        """
        command = f'{CMD_SCREEN_QUERY} | grep "{SCREEN_1} connected"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)

        match = re.match(REGEX_XRANDR, result.stdout.strip())

        if not match:
            return {}

        return {
            "x" : match.group('x_resolution'),
            "y" :  match.group('y_resolution'),
            "orientation" : match.group("orientation"),
        }

    def set_orientation(self, orientation: str):
        """
        Sets the screen orientation.
        """
        self.__update_line(
            CONFIG_XINITRC,
            CMD_SCREEN_1_ON,
            CMD_SCREEN_1_ON + f" --rotate {orientation}")

    def reload(self):
        """
        Restarts the window manager.
        """
        subprocess.run(f"systemctl restart {CONFIG_WM_SERVICE_FILE}", shell=True, check=True)
        #subprocess.run("systemctl restart kiosk-browser.service", shell=True, check=True)
