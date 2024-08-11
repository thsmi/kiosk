"""
Manages all configuration related data.
"""

import json
import hashlib
from pathlib import Path
import subprocess
import uuid

DEFAULT_SENSOR_DELAY = 30

class ConfigException(Exception):
    """
    Thrown in case of a configuration error.
    """

class Config():
    """
    Manages the configuration related data.
    """

    def __init__(self):
        # Ugly hack to get an guaranteed absolute path
        self.__root = Path(str(Path("/etc/kiosk").resolve()))
        if not self.__root.exists():
            self.__root.mkdir(exist_ok=True, parents=True)

        print(f"Config directory : {self.__root}")

    def get_root(self):
        """
        Gets the root folder for the configuration.
        """
        return self.__root

    def read_config(self, filename: str, defaults=None):
        """
        Reads a json configuration file
        """

        filename = self.get_root() / filename

        try:
            with open(filename, 'r', encoding="utf-8") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            if defaults is None:
                raise

            print(f"File '{filename}' not found. Returning default values.")
            return defaults

    def write_config(self, filename:str , data):
        """
        Writes a json configuration file.
        """
        filename =self.get_root() / filename

        with open(filename, 'w+', encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def get_config_value(self, filename:str, key:str, fallback):
        """
        Gets a specific value from a config file.
        """

        config = self.read_config(filename,{})

        if not key in config:
            return fallback

        return config[key]

    def set_config_value(self, filename:str, key:str, value):
        """
        Sets a specific value in the config file.
        """
        config = self.read_config(filename,{})
        config[key] = value

        self.write_config(filename, config)

    def enable_motion_sensor(self):
        """
        Enables the motion sensor
        """
        self.set_config_value("motionsensor.json", "enabled", True)

    def disable_motion_sensor(self):
        """
        Disables the motion sensor
        """
        self.set_config_value("motionsensor.json", "enabled", False)

    def is_motion_sensor_enabled(self) -> bool:
        """
        Checks if the motion sensor is enabled.
        """
        return self.get_config_value("motionsensor.json", "enabled", False)

    def get_motion_sensor_delay(self) -> float:
        """
        Gets the currently set motion sensor delay.
        """
        return self.get_config_value("motionsensor.json", "delay", DEFAULT_SENSOR_DELAY)

    def set_motion_sensor_delay(self, delay:float):
        """
        Sets the currently set motion sensor delay.
        """
        self.set_config_value("motionsensor.json", "delay", delay)

    def hash_password(self, password:str) -> str:
        """
        Secures the salted password with a sha256 hash
        """
        # Salt the password with the pi's serial number
        # to prevent passing the hash attacks.

        password += self.get_salt()

        return hashlib.sha256(
            password.encode("utf-8")).hexdigest()


    def set_password(self, password:str):
        """
        Writes the password to the config.
        """
        self.write_config(
            "password.json", 
            { "password" : self.hash_password(password)})


    def is_password(self, password:str) -> bool:
        """
        Checks if the password matches.
        """
        config = self.read_config("password.json", {"password" : None})

        if (config["password"] is None) and (password == "admin"):
            return True

        checksum = self.hash_password(password)

        if checksum == config["password"]:
            return True

        return False

    def get_salt(self):
        """
        Gets the serial number as pseudo random seed.
        """

        with open('/proc/cpuinfo', 'r', encoding="utf-8") as file:
            for line in file:
                if not line.startswith('Serial'):
                    continue

                serial = line.split(':')[1].strip()
                return serial

        raise ConfigException("Failed to retrieve serial number")

    def get_secret_key(self):
        """
        Retrieves the secret key used to protect the session.
        """
        filename = self.__root / "session.json"

        if not filename.exists():
            self.write_config("session.json", str(uuid.uuid4()))

        return self.read_config("session.json")

    def get_log(self, service:str) -> str:
        """
        Gets the log message for th given service.
        """
        try:
            return subprocess.run(
                ['journalctl', '-u', service, "--lines=200", "--reverse", "--no-pager", "--output=cat","--all"],
                capture_output=True, text=True, check=True).stdout

        except subprocess.CalledProcessError as e:
            print(f"Error occurred while reading journalctl log: {e.stderr}")
        except Exception as e:
            print(f"An error occurred: {e}")

        return "Failed to load log file"
