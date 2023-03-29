#!/bin/sh

pyside6-uic filter_info/ui/ui_window_main.ui  -o filter_info/ui/window_main_ui.py

export NO_AT_BRIDGE=1
python filter_info.py
