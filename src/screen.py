"""
Controls what is displayed on the screen, in explicit the the X11 session as well as the browser.
"""
import subprocess
import pathlib
import re

CONFIG_BROWSER = pathlib.Path("/etc/kiosk/browser.conf")
CONFIG_XINITRC = pathlib.Path("/etc/kiosk/xinitrc")

REGEX_XRANDR =  r"^HDMI-1 connected primary (?P<x_resolution>\d+)x(?P<y_resolution>\d+)\S+ \S+ (?P<orientation>\S+)"

CMD_DISPLAY_ON = "DISPLAY=:0 xset dpms force on && xset s off && xset -dpms && xset s noblank"
CMD_DISPLAY_OFF = "DISPLAY=:0 xset dpms force off"

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

    def get_screenshot(self, scale: int = None,  picture_format: str = None) -> bytes:
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
        #subprocess.run(["/bin/bash", "-c", CMD_DISPLAY_ON], check=True)
        subprocess.run(["/bin/bash", "-c", "DISPLAY=:0 xset dpms force on"], check=True)
        subprocess.run(["/bin/bash", "-c", "DISPLAY=:0 xset s off"], check=True)
        subprocess.run(["/bin/bash", "-c", "DISPLAY=:0 xset -dpms"], check=True)
        subprocess.run(["/bin/bash", "-c", "DISPLAY=:0 xset s noblank"], check=True)

    def off(self):
        """
        Turns the display off
        """

        subprocess.run(["/bin/bash", "-c", CMD_DISPLAY_OFF], check=True)


    def get_url(self):
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
        Sets the scale factor for high density displays
        """
        self.__update_line(
            CONFIG_BROWSER,
            "KIOSK_SCALE_FACTOR=",
            f'KIOSK_SCALE_FACTOR={scale}')

    def get_orientation(self) -> str:
        """
        Gets teh screen orientation an dimensions
        """
        command = 'xrandr --display :0 --query --verbose | grep " connected"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)

        match = re.match(REGEX_XRANDR, result.stdout.strip())

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
            "xrandr --output HDMI-1",
            f"xrandr --output HDMI-1 --rotate {orientation}")

    def reload(self):
        """
        Restarts the window manager.
        """
        subprocess.run("systemctl restart kiosk-windowmanager.service", shell=True, check=True)
        #subprocess.run("systemctl restart kiosk-browser.service", shell=True, check=True)
