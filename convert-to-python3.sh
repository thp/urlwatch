#!/bin/sh
# Convert urlwatch sources to Python 3.x compatible format

SOURCES="urlwatch lib/urlwatch/*.py share/urlwatch/examples/hooks.py.example setup.py"

2to3 -w $SOURCES

