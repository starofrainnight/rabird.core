'''
@date 2015-08-21
@author Hong-She Liang <starofrainnight@gmail.com>
'''


import os
import os.path
import platform
import subprocess

def _clean_check(cmd, target):
    """
    Run the command to download target. If the command fails, clean up before
    re-raising the error.
    """
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        if os.access(target, os.F_OK):
            os.unlink(target)
        raise

def download_file_powershell(url, target, headers=None):
    """
    Download the file at url to target using Powershell (which will validate
    trust). Raise an exception if the command cannot complete.
    """
    target = os.path.abspath(target)

    powershell_cmd = "$request = (new-object System.Net.WebClient);"
    for k, v in iter(headers):
        powershell_cmd += "$request.headers['%s'] = '%s';" % (k, v)    
    powershell_cmd += "$request.DownloadFile('%s', '%s')" % (url, target)
    
    cmd = [
        'powershell',
        '-Command',
        powershell_cmd, 
    ]
    
    _clean_check(cmd, target)

def has_powershell():
    if platform.system() != 'Windows':
        return False
    cmd = ['powershell', '-Command', 'echo test']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except:
            return False
    finally:
        devnull.close()
    return True

download_file_powershell.viable = has_powershell

def download_file_curl(url, target, headers=None):
    cmd = ['curl', url, '--silent', '--output', target]
    if headers is not None:
        if 'User-Agent' in headers:
            cmd += ['-A', '"%s"' % headers['User-Agent']]
        
    _clean_check(cmd, target)

def has_curl():
    cmd = ['curl', '--version']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except:
            return False
    finally:
        devnull.close()
    return True

download_file_curl.viable = has_curl

def download_file_wget(url, target, headers=None):
    cmd = ['wget', url, '--quiet']
    
    if headers is not None:
        if 'User-Agent' in headers:
            cmd += ['--user-agent="%s"' % headers['User-Agent']]
            
    cmd += ['--output-document', target]
    
    _clean_check(cmd, target)

def has_wget():
    cmd = ['wget', '--version']
    devnull = open(os.path.devnull, 'wb')
    try:
        try:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
        except:
            return False
    finally:
        devnull.close()
    return True

download_file_wget.viable = has_wget

def download_file_insecure(url, target):
    """
    Use Python to download the file, even though it cannot authenticate the
    connection.
    """
    download_file_insecure_to_io(url, open(target, "wb"))

download_file_insecure.viable = lambda: True

def get_best_downloader():
    downloaders = [
        download_file_powershell,
        download_file_curl,
        download_file_wget,
        download_file_insecure,
    ]

    for dl in downloaders:
        if dl.viable():
            return dl
        
def download(url, target=None):
    downloader = get_best_downloader()
    
    if target is None:
        target = os.path.basename(url)
        
    downloader(url, target)
    
def download_file_insecure_to_io(url, target_file=None, headers=None):
    """
    Use Python to download the file, even though it cannot authenticate the
    connection.
    """
    
    try:
        from urllib.request import urlopen
        from urllib.request import Request
    except ImportError:
        from urllib2 import urlopen
        from urllib2 import Request
    src = None
    try:
        req = Request(
            url, 
            data=None, 
            headers=headers
        )
        
        src = urlopen(req)
        
        # Read/write all in one block, so we don't create a corrupt file
        # if the download is interrupted.
        data = src.read()
        target_file.write(data)
    finally:
        if src:
            src.close()   
    