'''

Provided c-style string process methods.

@date 2015-03-22
@author Hong-She Liang <starofrainnight@gmail.com>
'''

def escape(text):
    return text.encode('unicode-escape').replace('"', '\\"')

def unescape(text):
    return text.decode('unicode-escape')    
        