#!/bin/sh

git clone https://github.com/nitmir/btdht.git

cp dht.pyx btdht/btdht/dht.pyx
cp setup.py btdht/setup.py
cp Makefile btdht/Makefile

sudo apt install python3-pip
pip install -r btdht/requirements-dev.txt

make install -C btdht
pip install twine

twine upload btdht/dist/*
pip install btdht
