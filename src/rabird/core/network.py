'''
@date 2015-03-17
@author Hong-She Liang <starofrainnight@gmail.com>
'''

import subprocess
import re
import sys
import struct

class ArpResolveError(KeyError):
    pass

def mac_to_text(mac_address, separator=''):
    elements = []
    for c in mac_address:
        # If the generated hex only have one charactor, we prefix with a "0".  
        elements.append(('00%s' % hex(ord(c))[2:])[-2:])
    
    return separator.join(elements).upper()

def text_to_mac(text):
    matched = re.findall('[0-9A-Fa-f]{1,2}', text)
    if len(matched) < 6:
        raise ValueError("")
    
    mac = []
    for i in xrange(0, 6):
        mac.append(chr(int(matched[i], 16)))
        
    return struct.pack('cccccc', *mac)

'''
Resolve the host to MAC address.

@note: This method depends on "arp" and "ping" commands, and it's slow.

All ARP related functions are all have some limitations:

1. In Windows

Windows XP SP2 (and greater) no longer natively support raw sockets,
We use a trick to get the arp result, not by a programming

2. In Unix

May require the root abilities

So we use a simple trick to get what want :  

1. Ping the IP, neither it success or not, arp entry appear in arp cache if
the IP existed in local network.

2. Find the IP and matched MAC in arp cache.

Because the "arp" and "ping" program commons around windows and unix, and 
does not required administration rights.  
  
'''
def arp_resolve(host):
    if sys.platform == "win32":
        subprocess.check_output(["ping", "-n", "1", host])
        output = subprocess.check_output(["arp", "-a"])
    else:
        subprocess.check_output(["ping", "-c", "1", host])
        output = subprocess.check_output(["arp"])
        
    mac_expr = r'\D%s\D.*((?:[0-9a-fA-F]{2}[^0-9a-fA-F]+){5}[0-9a-fA-F]{2})' % re.escape(host)        
    matched = re.search(mac_expr, output)
    if matched is not None:
        return text_to_mac(matched.group(1))
        
    raise ArpResolveError("Failed to resolve for %s" % host)
    