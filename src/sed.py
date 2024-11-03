"""
Parses a line based config file or script.
"""

import pathlib


class SingleLineEditor():
    """
    A simplistic single line editors which allows getting and updating lines in a config file.
    """

    def __init__(self, filename: pathlib.Path):
        self.__filename = filename

    def get_line(self, search:str):
        """
        Parses the file and returns the line starting with the search string.
        """
        if  not self.__filename.exists():
            return None

        with self.__filename.open('r', encoding="utf-8") as file:
            for line in file:
                if not line.startswith(search):
                    continue

                return line

        return None

    def update_line(self, search:str, replacement:str):
        """
        Parses the file and updates the line starting with the search string.
        """
        with self.__filename.open('r', encoding="utf-8") as file:
            lines = file.readlines()

        # Modify the line that starts with KIOSK_HOME=
        with self.__filename.open('w', encoding="utf-8") as file:
            for line in lines:
                if line.startswith(search):
                    file.write(replacement+"\n")
                    continue

                file.write(line)
