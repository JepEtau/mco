#!/bin/sh
PYENV_PATH="$(realpath ~/.pyenv/bin)"
export PATH="$PYENV_PATH:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
cd ~/mco/tools

python3 ~/mco/tools/filter_info.py $1
