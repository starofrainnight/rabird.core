'''
@date 2015-08-20
@author Hong-She Liang <starofrainnight@gmail.com>
'''

import re
import os
import sys
import math
import urllib
import pip
import pkg_resources
import struct
import platform
import six
from setuptools.command.install import install as distutils_install
from setuptools.command.easy_install import is_64bit
from pkg_resources._vendor.packaging.version import Version
from ..utils import easy_download
from pip.wheel import Wheel
try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    from urllib import urlopen
    
class UwbpepPackages(object):
    def __init__(self, content):
        re_flags = re.DOTALL|re.MULTILINE
        matched = re.search('<ol class="inline">(.*?)</ol>', content, re_flags)
        package_names = re.findall('<a href="#.*?>(.*?)</a>', matched.group(1), re_flags)
        matched = re.findall('javascript:dl\(\[(.*?)\], "(.*?)"\)', content, re_flags)
        
        base_url = "http://www.lfd.uci.edu/~gohlke/pythonlibs"
        
        open("kknd.html", "wb").write(content.encode("utf-8"))
        
        # Initialize packages with names
        packages = {}
        package_groups = {}

        # Decrypt links
        for amatch in matched:
            numbers = []
            number_texts = amatch[0].split(",")
            for number_text in number_texts:
                numbers.append(int(number_text))
                        
            url = os.path.join(base_url, self._decode_url(numbers, amatch[1]))
            filename = os.path.basename(url)
            
            filebasename, fileextname = os.path.splitext(filename)
            if "pywin32" in filebasename:
                print(amatch[0])
                print(amatch[1])
                print(url)
                    
            if fileextname not in [".whl", ".exe"]:
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
                
            wheel = Wheel(filename)
            
            package_name = wheel.name.lower().replace("_", "-")
            if package_name not in packages:
                packages[package_name] = {}
                packages[package_name]["wheels"] = []
                packages[package_name]["requirements"] = []  
            
            packages[package_name]["wheels"].append((wheel, url))
            
        # Analyse dependences
        matched = re.findall('<li>(<a id=.*?)<li>', content, re_flags)
        for amatch in matched:
            if 'Requires <a href="#' not in amatch:
                continue
            
            package_name = re.search('<a id=["\'](.*?)["\']>', amatch).group(1)   
            requirements = re.findall('<a href="#(.*?)">', amatch)
            try:
                packages[package_name]["requirements"] = requirements
            except KeyError:
                # FIXME: We should record the package groups, otherwise some requirement
                # can't be found!
                pass
            
        self.packages = packages        
        
    def _decode_url(self, ml, mi):        
        mi = mi.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&')
        
        ot=""
        for j in range(0, len(mi)):
            ot += chr(ml[ord(mi[j])-48])
            
        return ot
        
    def search_url(self, requirement_text):
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
            
            return url
        
        raise KeyError("Can't find the requirement : %s" % requirement_text)
            

class install(distutils_install):
    """
    
    Abbreviations:
    
    uwbpep : Unofficial Windows Binaries for Python Extension Packages
    
    http://www.lfd.uci.edu/~gohlke/pythonlibs/
    """

    def download_file(self, url):
        """Helper to download large files
        the only arg is a url
        the downloaded_file will also be downloaded_size
        in chunks and print out how much remains
        """
        
        downloaded_blocks = []
        
        try:
            req = urllib.request.urlopen(url)
            
            if six.PY2:
                total_size = int(req.info().getheader("Content-Length").strip())
            else:
                total_size = int(req.getheader("Content-Length").strip())
                
            downloaded_size = 0
            block_size = 16 * 1024 # 16k each chunk
            
            print("Total size : %s" % (total_size))
            
            while True:
                readed_buffer = req.read(block_size)
                if not readed_buffer:
                    break
                
                downloaded_size += len(readed_buffer)
                
                print("Downloaded : %s%%" % (math.floor((float(downloaded_size) / float(total_size)) * 100)))
                
                downloaded_blocks.append(readed_buffer)
                    
        except urllib.error.HTTPError as e:
            print("HTTP Error: %s %s" % (e.code, url))
            return False
        except urllib.error.URLError as e:
            print("URL Error: %s %s" % (e.reason, url))
            return False
        
        return b''.join(downloaded_blocks)
    
    def run(self):        
        # Try to use pip install first
        failed_requires = [] 
        for arequire in self.distribution.install_requires:
            
            # pip.main() will return 0 while successed ..
            if pip.main(["install", arequire]) != 0:
                failed_requires.append(arequire)
            
        failed_requires.append("pywin32")
        if len(failed_requires) > 0:
            print('Downloading list page of "Unofficial Windows Binaries for Python Extension Packages" ...')
            content = self.download_file("http://www.lfd.uci.edu/~gohlke/pythonlibs").decode('utf-8')
            print("Download finished. \nParsing ...")
            packages = UwbpepPackages(content)
              
            # Try to install failed requires from UWBPEP    
            for arequire in failed_requires:                
                url = packages.search_url(arequire)
                filename = os.path.basename(url)
#                 easy_download(url)
#                 if '.whl' == os.path.splitext(filename)[1]:
#                     pip.main("install", filename)
                                
        # self.distribution.install_requires
#         distutils_install.run(self)
        
        