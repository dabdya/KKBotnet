#!/bin/sh

sudo touch /etc/systemd/system/botnet.service;
sudo apt-get update
sudo apt install net-tools
sudo ufw disable
cfg="[Unit]
Description=botnet
After=network.target

[Service]
User='$(whoami)'
Group='$(id -g)'
WorkingDirectory='$(pwd)'
ExecStart=/usr/bin/python3 $(pwd)/src/main.py --port=$(sudo netstat -tulpn | grep LISTEN | grep transmission | awk '{split($0,arr,":"); print arr[4]}')
TimeoutSec=30
Restart=always

[Install]
WantedBy=multi-user.target"

sudo apt install python3-pip
sudo pip install -r requirements.txt

sudo bash -c "echo '$cfg' > /etc/systemd/system/botnet.service";
echo "$cfg"
sudo systemctl enable botnet
sudo systemctl start botnet
