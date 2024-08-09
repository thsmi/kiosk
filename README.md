# Information Kiosk

Simplistic Kiosk Mode for Ubuntu/Debian

## Install

As prerequisites you need a headless Raspberry Pi OS, a Ubuntu or Debian.

Then clone the repository and then call the setup.sh with sudo permissions.

It will install a window manager, chromium and a python based web service along with all tools needed.
The chromium process runs as user "kiosk" in case the user does not exist it will be created.
It will also activate automatic updates.

Currently only one display on the first HDMI port is supported.


