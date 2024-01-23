#!/bin/sh
cd linien-common
pip install -e .
cd ../linien-client
pip install -e .
cd ../linien-gui
pip install -e .
pip install git+https://github.com/m-labs/misoc
pip install git+ssh://git@github.com/elhep/Fast-Servo-Firmware.git