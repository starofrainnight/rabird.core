'''
@date 2013-5-9

@author Hong-She Liang <starofrainnight@gmail.com>
'''

import sys
import os

# Import the global logging unit, not our logging .
global_logging = __import__('logging')


def load_default_config():
    arguments = {
        'level': None,
        'filename': None,
        'filemode': None,
        'format': None,
        'datefmt': None,
        'style': None,
    }

    for k in list(arguments.keys()):
        try:
            envionment_text = 'PYTHON_LOGGING_%s' % k.upper()
            arguments[k] = os.environ[envionment_text]
        except ValueError:
            pass
        except KeyError:
            pass

    # Remove all arguments that is None value.
    keys = list(arguments.keys())
    for k in keys:
        if arguments[k] is None:
            del arguments[k]

    # Set default level to logging.INFO .
    if 'level' not in list(arguments.keys()):
        arguments['level'] = global_logging.INFO

    global_logging.basicConfig(**arguments)

    # Added console handler only there have filename argument.
    if 'filename' in list(arguments.keys()):
        global_logging.getLogger().addHandler(global_logging.StreamHandler(sys.stdout))
