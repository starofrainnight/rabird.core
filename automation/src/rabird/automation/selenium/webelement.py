
#--IMPORT_ALL_FROM_FUTURE--#

'''
@date 2014-11-16
@author Hong-she Liang <starofrainnight@gmail.com>
'''

# Import the global selenium unit, not our selenium .
global_selenium = __import__('selenium')
import types
import time
from . import utilities

def set_attribute(self, name, value):
    value = utilities.js_string_encode(value)
    script = "arguments[0].setAttribute('%s', '%s');"  % (name, value)
    self._parent.execute_script(script, self)

def force_focus(self):
    self._parent.execute_script("arguments[0].focus();", self);

def force_click(self):
    self._parent.execute_script("arguments[0].click();", self);
        