# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import platform


def get_process_cfg():
    if hasattr(subprocess, 'STARTUPINFO'):
        startupInfo = subprocess.STARTUPINFO()
        startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupInfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
        osEnvironment = os.environ
    else:
        startupInfo = None
        osEnvironment = None
    return {
        'startupInfo': startupInfo,
        'osEnvironment': osEnvironment,
    }


def create_process(command, process_cfg, bufsize=10**7):

    if platform.system() == "Windows":
        process = subprocess.Popen(command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=process_cfg['osEnvironment'],
            startupinfo=process_cfg['startupInfo'],
            bufsize=bufsize)

    elif sys.platform == 'linux':
        process = subprocess.Popen(command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=process_cfg['osEnvironment'],
            startupinfo=process_cfg['startupInfo'],
            bufsize=bufsize
            )
    return process


