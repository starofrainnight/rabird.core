
import sys

__version__ = '0.3.15'
__monkey_patched = False

# Known Issues : Can't work with eventlet, Why?


def monkey_patch():
    global __monkey_patched

    if __monkey_patched:
        return

    if sys.platform == 'win32':
        from . import windows_api
        from . import windows_fix

        if sys.version_info[0] <= 2:
            windows_fix.monkey_patch()

        __monkey_patched = True
