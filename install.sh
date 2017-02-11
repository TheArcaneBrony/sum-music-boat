#!/bin/bash

apt install gcc make ffmpeg python3.5-dev -y

wget https://bootstrap.pypa.io/get-pip.py
python3.5 get-pip.py
pip3.5 install cffi youtube-dl cleverbot langdetect discord.py[voice] bs4