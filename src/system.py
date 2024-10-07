"""
Manages system wide settings like host name or reboots 
"""

from pathlib import Path
import subprocess
import threading
import time

ETC_HOSTNAME = Path("/etc/hostname")
ETC_HOSTS = Path("/etc/hosts")


class System:
    """
    Manages system wide helper functions.
    """

    def enable_ssh(self):
        """
        Enables the ssh service
        """
        subprocess.run(["systemctl", "enable", "ssh"], check=False)
        subprocess.run(["systemctl", "start", "ssh"], check=False)

    def disable_ssh(self):
        """
        Disables the ssh service
        """
        subprocess.run(["systemctl", "disable", "ssh"], check=False)
        subprocess.run(["systemctl", "stop", "ssh"], check=False)

    def is_ssh_active(self):
        """
        Checks if ssh is active
        """
        rv = subprocess.run(["systemctl", "is-active", "--quiet", "ssh"], check=False)
        return rv.returncode == 0

    def reboot(self):
        """
        Reboots the system with a short delay.
        It is need to give http enough time so send a response to the client.
        """
        def reboot_task():
            print("Rebooting in 5 seconds...")
            time.sleep(5)
            subprocess.run("reboot", check=False)

        reboot_thread = threading.Thread(target=reboot_task)
        reboot_thread.start()

    def set_hostname(self, hostname:str):
        """
        Sets a hostname 
        """

        # Update /etc/hostname
        with ETC_HOSTNAME.open('w', encoding="utf-8") as file:
            file.write(f'{hostname}\n')

        # Update /etc/hosts
        with ETC_HOSTS.open('r', encoding="utf-8") as file:
            hosts_content = file.readlines()

        with ETC_HOSTS.open('w', encoding="utf-8") as file:
            for line in hosts_content:
                if line.startswith('127.0.1.1'):
                    file.write(f'127.0.1.1\t{hostname}\n')
                else:
                    file.write(line)

    def get_hostname(self):
        """
        Gets the current hostname
        """
        with ETC_HOSTNAME.open('r', encoding="utf-8") as file:
            return file.readline()
