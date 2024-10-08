#!/bin/bash
set -e

if [ `id -u` -ne 0 ]
  then echo Please run this script as root or using sudo.
  exit
fi

update_system() { 
  echo Update System

  apt-get update -qq
  apt-get full-upgrade -yy -qq
  apt-get autoremove -yy -qq

  apt-get install unattended-upgrades -yy -qq
  apt-get install fail2ban -yy -qq
}

install_window_manager() {
  echo Installing Window Manager

  apt-get install --no-install-recommends xserver-xorg xinit x11-xserver-utils -yy -qq
  apt-get install matchbox-window-manager -yy -qq
  apt-get install unclutter -yy -qq

  mkdir -p /etc/kiosk
  cat > /etc/kiosk/xinitrc << EOF
#!/bin/sh

xrandr --output HDMI-1
xrandr --output HDMI-2 --off

# Turn off screensaver
xset s off
# Disable DPMS (Energy Star) features
xset -dpms
# Disable screen blanking
xset s noblank

unclutter &

exec /usr/bin/matchbox-window-manager -use_titlebar no -- :0
EOF


  cat > /etc/systemd/system/kiosk-windowmanager.service << EOF
[Unit]
Description=Matchbox Window Manager
After=network.target

[Service]
User=root
Environment=DISPLAY=:0
ExecStart=/usr/bin/xinit /etc/kiosk/xinitrc --
Restart=always

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable kiosk-windowmanager.service
}

install_browser() {
  echo Installing Browser

  if ! id "kiosk" &>/dev/null; then
    # Create the user 'kiosk' if it doesn't exist
    useradd -m kiosk
  fi

  apt-get install chromium-browser -yy -qq

  cat > /etc/kiosk/browser.conf << EOF
KIOSK_HOME=https://www.example.com/
KIOSK_SCALE_FACTOR=1.0
EOF

  cat > /etc/systemd/system/kiosk-browser.service << EOF
[Unit]
Description=Kiosk Mode
After=network.target kiosk-windowmanager.service
Requires=kiosk-windowmanager.service

[Service]
User=kiosk
EnvironmentFile=/etc/kiosk/browser.conf
Environment=DISPLAY=:0

# In case chromium crashed it may have endup with an open session. 
# Which prevents chromium from starting.
ExecStartPre=/bin/bash -c "rm -rf ~/.config/chromium/Singleton*"

ExecStart=/bin/bash -c "/usr/bin/chromium-browser --hide-scrollbars --high-dpi-support=1 --force-device-scale-factor=\$KIOSK_SCALE_FACTOR --enable-offline-auto-reload --kiosk --incognito --window-position=0,0 \$KIOSK_HOME"

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable kiosk-browser.service
}

install_application() {
  echo Installing Application

  # Needed to convert screenshots.
  apt-get install imagemagick x11-apps -yy -qq

  # Install python
  mkdir -p /opt/kiosk
  python -mvenv /opt/kiosk/.venv 

  /opt/kiosk/.venv/bin/pip install flask --quiet

  cp __init__.py /opt/kiosk/

  mkdir -p /opt/kiosk/src
  cp -r ./src/ /opt/kiosk/

  mkdir -p /opt/kiosk/html
  cp -r ./html/ /opt/kiosk/

  cat > /etc/systemd/system/kiosk-webservice.service << EOF
[Unit]
Description=Webservice to control Kiosk
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/kiosk/
ExecStart=/opt/kiosk/.venv/bin/python3 /opt/kiosk/__init__.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

  cat > /etc/cron.d/kiosk << EOF
# Autogenerated do not change manually.

0 5 * * 1,2,3,4,5 root /sbin/shutdown -r now
0 22 * * 1,2,3,4,5 root DISPLAY=:0 xset dpms force off
EOF

  systemctl daemon-reload
  systemctl enable kiosk-webservice.service
}

update_system
install_window_manager
install_browser
install_application

reboot
