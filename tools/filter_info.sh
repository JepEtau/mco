#!/bin/sh
# pyside6-uic filter_info/ui/ui_window_main.ui  -o filter_info/ui/window_main_ui.py

PYENV_PATH="$(realpath ~/.pyenv/bin)"
export PATH="$PYENV_PATH:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
cd ~/mco/tools

python3 ~/mco/tools/filter_info.py $1
