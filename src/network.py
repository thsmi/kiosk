"""
Configures the wifi an ethernet connection. 
It expects that the network manager is installed.
"""

import re
import subprocess

class NetworkEthernetConnection():
    """
    Realizes an ethernet connection.
    """

    def __init__(self, name):
        self.__name = name
        self.__data = {}

    def get_name(self):
        """
        Returns the connection name.
        """
        return self.__name

    def get_type(self):
        """
        Returns the connection type.
        """
        return "Ethernet"

    def get_value(self, key) -> str:
        """
        Returns the value where the key is an exact match.
        """
        if len(self.__data) == 0:
            self.load()

        if key not in self.__data:
            return None

        return self.__data[key]

    def get_values(self, pattern: re.Pattern) -> str:
        """
        Returns the values for all keys which match the given pattern.
        """
        if len(self.__data) == 0:
            self.load()

        result = []
        for key, value in self.__data.items():
            if not re.match(pattern, key):
                continue

            result.append(value)

        return result


    def load(self):
        """
        Load the connection information.
        """
        connection = subprocess.run(
            f'nmcli -t connection show "{self.__name}"' , shell=True,
            capture_output=True, text=True, check=False).stdout.strip()

        self.__data.clear()
        for line in connection.splitlines():
            line = line.split(":",1)
            self.__data[line[0]] = line[1]

        return self

    def get_ip4_addresses(self) -> list[str]:
        """
        Gets all IPv4 Addresses for the connection.
        """
        return self.get_values(r"IP4\.ADDRESS\[\d+\]")

    def get_ip4_gateway(self) -> str:
        """
        Gets the IPv4 Gateways Address for the connection.
        """
        return self.get_value("IP4.GATEWAY")

    def get_ip4_dns(self) -> list[str]:
        """
        Gets the IPv4 DNS Servers.
        """
        return self.get_values(r"IP4\.DNS\[\d+\]")

    def get_ip6_addresses(self) -> list[str]:
        """
        Gets the IPv6 addresses.
        """
        return self.get_values(r"IP6\.ADDRESS\[\d+\]")

    def get_ip6_gateway(self) -> str:
        """
        Gets the IPv6 Gateway address for the connection.
        """
        return self.get_value("IP6.GATEWAY")

    def get_ip6_dns(self) -> list[str]:
        """
        Gets the IPv6 DNS Servers.
        """
        return self.get_values(r"IP6\.DNS\[\d+\]")

    def get_state(self) -> str:
        """
        Returns the connections current state
        """
        return self.get_value("GENERAL.STATE")

    def is_default(self) -> str:
        """
        Checks if the connection is the default connection.
        """
        return self.get_value("GENERAL.DEFAULT")

    def to_serializable_object(self):
        """
        Convert the connection into a serializable object.
        """
        return {
            "name" : self.get_name(),
            "type" : self.get_type(),
            "state" : self.get_state(),
            "default" : self.is_default(),
            "ipv4" : {
                "addresses" : self.get_ip4_addresses(),
                "gateway" : self.get_ip4_gateway(),
                "dns" : self.get_ip4_dns()
            },
            "ipv6" : {
                "addresses" : self.get_ip6_addresses(),
                "gateway" : self.get_ip6_gateway(),
                "dns" : self.get_ip6_dns()
            }
        }


class NetworkWifiConnection(NetworkEthernetConnection):
    """
    Realizes a wifi connection.
    """

    def get_type(self):
        return "Wifi"

    def get_ssid(self) -> str:
        """
        Returns the wifi networks ssid.
        """
        return self.get_value("802-11-wireless.ssid")

    def to_serializable_object(self):
        data = super().to_serializable_object()
        data["ssid"] = self.get_ssid()
        return data


class Network():
    """
    Abstracts the network interface.
    """

    def get_connections(self):
        """
        Returns a list of all configured connections.
        """

        devices = subprocess.run(
            "nmcli -t device", shell=True,
            capture_output=True, text=True, check=False).stdout.strip()

        rv = []

        for device in  devices.split("\n"):
            data = device.split(":")

            if data[1] == "wifi":
                if data[3].strip() == "":
                    continue

                rv.append(NetworkWifiConnection(data[3]))
                continue

            if data[1] == "ethernet":
                rv.append(NetworkEthernetConnection(data[3]))
                continue

        return rv

    def delete_wifi_connection(self, ssid:str, fail_on_error=None):
        """
        Deletes the wifi connection with the given name.
        """

        if fail_on_error is None:
            fail_on_error = True

        subprocess.run(
            f'nmcli connection delete "{ssid}"',
            shell=True, check=fail_on_error)

    def delete_wifi_connections(self):
        """
        Deletes all wifi connections.
        """
        connections = subprocess.run(
            "nmcli -t -f TYPE,NAME connection show", shell=True,
            capture_output=True, text=True, check=True).stdout.strip()

        for connection in connections.splitlines():
            connection = connection.split(":")

            if connection[0] != "802-11-wireless":
                continue

            self.delete_wifi_connection(connection[1])

    def add_wifi_connection(self, ssid:str, psk:str):
        """
        Adds a new wifi connection
        """

        self.delete_wifi_connection(ssid, False)

        subprocess.run(
            f'nmcli device wifi connect "{ssid}" password "{psk}"',
            shell=True, check=True)
