'''
@date 2015-08-20
@author Hong-She Liang <starofrainnight@gmail.com>
'''

import re
import os
import io
import sys
import math
import urllib
import pip
import pkg_resources
import struct
import platform
import six
from six.moves import urllib
from setuptools.command.install import install as distutils_install
from setuptools.command.easy_install import is_64bit
from pkg_resources._vendor.packaging.version import Version
from ..downloader import download, download_file_insecure_to_io
if sys.platform == "win32":
    from ... import windows_api
from pip.wheel import Wheel

class BaseUwbpepServer(object):
    def __init__(self):
        pass
    
    def _get_page_url(self):
        raise NotImplemented()   
    
    def _get_headers(self):
        return {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'}   
    
    def _parse_urls(self, content):
        raise NotImplemented()
    
    def _decode_url_and_filename(self, amatch):
        raise NotImplemented()
    
    def _get_index_page(self):
        bytes_io = io.BytesIO()            
        try:
            download_file_insecure_to_io(
                self._get_page_url(), 
                bytes_io, 
                # If you pass a wrong user agent, 
                headers=self._get_headers(),
                )
            return bytes_io.getvalue().decode('utf-8')  
        finally:
            bytes_io.close()
            
    def connect(self):
        print('Downloading list page of "Unofficial Windows Binaries for Python Extension Packages" ...')
        
        content = self._get_index_page()
            
        print("Download finished. \nParsing ...")
            
        matches = self._parse_urls(content)
        
        # Initialize packages with names
        packages = {}

        # Decrypt links
        for amatch in matches:
            url, filename = self._decode_url_and_filename(amatch)
            
            filebasename, fileextname = os.path.splitext(filename)
            if fileextname not in [".whl", ".zip", ".exe"]:
                continue
            
            if len(filename.split("-")) < 5:
                continue
            
            if fileextname == ".exe":
                # Fixed *.exe name to fit for Wheel() requirement! A slight trick
                # to support *.exe package. 
                
                filebasename = filebasename.replace('.win-amd64', '-win_amd64')
                filebasename = filebasename.replace('.win', '-win')
                filebasename = filebasename.replace('-py2.', '-cp2')
                filebasename = filebasename.replace('-py3.', '-cp3')
                
                wheel_info = filebasename.split('-')
                filename = "%s-%s-%s-%s-%s.whl" % (
                    wheel_info[0],
                    wheel_info[1],
                    wheel_info[3],
                    'none',
                    wheel_info[2]
                    )
            elif fileextname == ".zip":
                filename = "%s%s" % (filebasename, ".whl")
                
            wheel = Wheel(filename)
            
            package_name = wheel.name.lower().replace("_", "-")
            if package_name not in packages:
                packages[package_name] = {}
                packages[package_name]["wheels"] = []
                packages[package_name]["requirements"] = []  
            
            packages[package_name]["wheels"].append((wheel, url))
            
        self.packages = packages  
        
    def _find_package(self, requirement_text):
        requirement = pkg_resources.Requirement.parse(requirement_text)
        wheel_contexts = self.packages[requirement.key]["wheels"]
        
        if is_64bit():
            python_platform = "64"
        else:
            python_platform = "32"
            
        python_versions = set([
            "cp%s" % platform.python_version_tuple()[0],
            "cp%s%s" % (platform.python_version_tuple()[0], platform.python_version_tuple()[1]),
            "py%s" % platform.python_version_tuple()[0],
            "py%s%s" % (platform.python_version_tuple()[0], platform.python_version_tuple()[1]),
            ])        
                
        for wheel, url in wheel_contexts:
            if python_platform not in wheel.plats[0]:
                continue
            
            if len(set(wheel.pyversions) & python_versions) <= 0:
                continue
            
            wheel_version = Version(wheel.version)
            if not requirement.specifier.contains(wheel_version):
                continue        
            
            return (wheel, url)
        
        raise KeyError("Can't find the requirement : %s" % requirement_text)
    
    def install(self, requirement):
        wheel, url = self._find_package(requirement)
        filename = wheel.filename
        
        print("Downloading ... %s " % url)

        download(url, filename, self._get_headers())
        
        pip.main(["install", filename])
        
        # Only pywin32 needs postinstall script. 
        if filename.startswith("pywin32"):
            postinstall_script_path = os.path.normpath(os.path.join(
                    sys.exec_prefix, 
                    "Scripts", 
                    "pywin32_postinstall.py"))
            postinstall_script_path = postinstall_script_path.replace("/", "\\")                    
            windows_api.RunAsAdmin([
                sys.executable, 
                postinstall_script_path], 
                True)

class PythonlibsUwbpepServer(BaseUwbpepServer):    
    page_url = "http://www.lfd.uci.edu/~gohlke/pythonlibs"
    
    def __init__(self):
        super(BaseUwbpepServer, self).__init__()
    
    def _decode_url(self, ml, mi):
        mi = mi.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&')
        
        ot=""
        for j in range(0, len(mi)):
            ot += chr(ml[ord(mi[j])-48])
            
        return ot
    
    def _get_page_url(self):
        return "http://www.lfd.uci.edu/~gohlke/pythonlibs"   
    
    def _parse_urls(self, content):
        re_flags = re.DOTALL|re.MULTILINE
        return re.findall(r'javascript:dl\(\[([^\]]*?)\],\s*"([^"]*?)"', content, re_flags)        
    
    def _decode_url_and_filename(self, amatch):
        ml = []    
        for number in amatch[0].split(","):
            ml.append(int(number))
            
        url = self._decode_url(ml, amatch[1])
        url = "%s/%s" % (self._get_page_url(), url)            
        filename = os.path.basename(url)
        
        return (url, filename)

class GithubUwbpepServer(BaseUwbpepServer):    
    def __init__(self):
        super(BaseUwbpepServer, self).__init__()
    
    def _get_page_url(self):
        return "https://github.com/starofrainnight/uwbpep/releases/tag/v1.0" 
    
    def _parse_urls(self, content):
        re_flags = re.DOTALL|re.MULTILINE
        return re.findall(r'<a href="([^"]*?)" rel="nofollow">', content, re_flags)        
    
    def _decode_url_and_filename(self, amatch):
        url_parties = list(urllib.parse.urlparse(self._get_page_url()))
        url_parties[2] = amatch
        url = urllib.parse.urlunparse(url_parties)
        filename = os.path.basename(url)
        
        return (url, filename)      
        
class PypiUwbpepServer(BaseUwbpepServer):    
    def __init__(self):
        super(BaseUwbpepServer, self).__init__()
    
    def _get_page_url(self):
        return "https://pypi.python.org/pypi/uwbpep/1.0" 
    
    def _parse_urls(self, content):
        re_flags = re.DOTALL|re.MULTILINE
        return re.findall(r'<a href="([^"]*?\.whl#md5=[^"]*?)"', content, re_flags)        
    
    def _decode_url_and_filename(self, amatch):
        url = amatch
        filename = os.path.basename(url.split("#")[0])
        # Removed the first "uwbpep1.0_" tag!
        filename = filename[len("uwbpep1.0_"):]
        
        return (url, filename)
        
class install(distutils_install):
    """
    The install command provide extension packages automatic install from
    our custom package page.
    
    We make a cached page at 
    
    https://github.com/starofrainnight/uwbpep/releases/tag/v1.0
    
    which copied some needed packages from 
    
    http://www.lfd.uci.edu/~gohlke/pythonlibs/

    Abbreviations:
    
    uwbpep : Unofficial Windows Binaries for Python Extension Packages
    
    """
    def _prepare_requirements(self):
        # Try to use pip install first
        failed_requires = [] 
        for arequire in self.distribution.install_requires:
            
            # pip.main() will return 0 while successed ..
            if pip.main(["install", arequire]) != 0:
                failed_requires.append(arequire)
            
        if len(failed_requires) > 0:
            server = PypiUwbpepServer()
            server.connect()            
              
            # Try to install failed requires from UWBPEP    
            for arequire in failed_requires:
                server.install(arequire)
                                
    def run(self):        
        if sys.platform == "win32":
            self._prepare_requirements()
            
        # self.distribution.install_requires
        distutils_install.run(self)
        
        