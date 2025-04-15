import os
import subprocess
import sys
import time
from warnings import warn


RESOLVE_SCRIPT_API = ""
if sys.platform == "darwin":
    RESOLVE_SCRIPT_API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"

elif sys.platform == "win32":
    RESOLVE_SCRIPT_API = os.path.join(
        os.environ["PROGRAMDATA"],
        "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules"
    )
    RESOLVE_EXE_PATH = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"

elif sys.platform == "linux":
    RESOLVE_SCRIPT_API = "/opt/resolve/Developer/Scripting/Modules/"

if RESOLVE_SCRIPT_API:
    sys.path.append(os.path.join(RESOLVE_SCRIPT_API, ))


try:
    # The PYTHONPATH needs to be set correctly for this import statement to work.
    # An alternative is to import the DaVinciResolveScript by specifying absolute path (see ExceptionHandler logic)
    import DaVinciResolveScript as bmd

except ImportError:
    # check if the default path has it...
    raise ValueError(f"Unable to find module DaVinciResolveScript from {RESOLVE_SCRIPT_API}")


_already_started: bool = True
def app_already_started() -> bool:
    """Returns True if DaVinci Resolve was already started before
        reunning the script
    """
    return _already_started



def get_resolve():
    resolve = bmd.scriptapp("Resolve")

    if not sys.platform == "win32":
        raise SystemError("DaVinci Resolve must be started before")

    if resolve is None:
        warn("DaVinci Resolve is not opened, try opening it")
        global _already_started
        _already_started = False
        subprocess.Popen(args=[f"\"{RESOLVE_EXE_PATH}\"", "-nogui"])

        time.sleep(1)
        resolve = bmd.scriptapp("Resolve")

    try:
        version = resolve.GetVersionString()

    except Exception as e:
        raise SystemError("Failed to start DaVinci Resolve")

    return resolve
