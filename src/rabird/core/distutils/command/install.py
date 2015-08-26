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
from ..utils import easy_download
from ... import windows_api
from pip.wheel import Wheel

def download_file(url, file=None):
    """Helper to download large files
    the only arg is a url
    the downloaded_file will also be downloaded_size
    in chunks and print out how much remains
    """
    
    if (file is None):
        file = open(os.path.basename(url), 'wb')        
    
    req = urllib.request.urlopen(url)
    
    downloaded_size = 0
    block_size = 16 * 1024 # 16k each chunk
    
    while True:
        readed_buffer = req.read(block_size)
        if not readed_buffer:
            break
        
        downloaded_size += len(readed_buffer)
        
        print("Downloaded : %s" % downloaded_size)

        file.write(readed_buffer)
    
class GithubUwbpepPackages(object):    
    page_url = "https://github.com/starofrainnight/uwbpep/releases/tag/v1.0"
    
    def __init__(self):
        pass
        
    def parse(self):
        print('Downloading list page of "Unofficial Windows Binaries for Python Extension Packages" ...')
        bytes_io = io.BytesIO()            
        try:
            download_file(self.page_url, bytes_io)
            content = bytes_io.getvalue().decode('utf-8')  
        finally:
            bytes_io.close()
            
        print("Download finished. \nParsing ...")
            
        re_flags = re.DOTALL|re.MULTILINE
        matched = re.findall('<a href="([^"]*?)" rel="nofollow">', content, re_flags)
        
        # Initialize packages with names
        packages = {}

        # Decrypt links
        for amatch in matched:
            url_parties = list(urllib.parse.urlparse(self.page_url))
            url_parties[2] = amatch
            url = urllib.parse.urlunparse(url_parties)
            filename = os.path.basename(url)
            
            filebasename, fileextname = os.path.splitext(filename)
            if fileextname not in [".whl", ".exe", ".zip"]:
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
            
class PypiUwbpepPackages(object):    
    page_url = "https://pypi.python.org/pypi/uwbpep/0.1.0"
    
    def __init__(self):
        pass
        
    def parse(self):
        print('Downloading list page of "Unofficial Windows Binaries for Python Extension Packages" ...')
        bytes_io = io.BytesIO()            
        try:
            download_file(self.page_url, bytes_io)
            content = bytes_io.getvalue().decode('utf-8')  
        finally:
            bytes_io.close()
            
        print("Download finished. \nParsing ...")
            
        re_flags = re.DOTALL|re.MULTILINE
        matched = re.findall('<a href="([^"]*?\.whl#md5=[^"]*?)"', content, re_flags)
        
        # Initialize packages with names
        packages = {}

        # Decrypt links
        for amatch in matched:
            url = amatch
            filename = os.path.basename(url.split("#")[0])
            # Removed the first "uwbpep" tag!
            filename = filename[len("uwbpep"):]
            print(filename)
            
            filebasename, fileextname = os.path.splitext(filename)
            if fileextname not in [".whl", ".exe", ".zip"]:
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
            packages = PypiUwbpepPackages()
            packages.parse()            
              
            # Try to install failed requires from UWBPEP    
            for arequire in failed_requires:                
                url = packages.search_url(arequire)
                filename = os.path.basename(url)
                print("Downloading ... %s " % url)

                if '.zip' == os.path.splitext(filename)[1]:
                    filebasename, fileextname = os.path.splitext(filename)
                    filename = "%s%s" % (filebasename, ".whl")
                
                easy_download(url, filename)
                
                pip.main(["install", filename])
                
                # Only pywin32 needs postinstall script. 
                if filename.startswith("pywin32"):
                    postinstall_script_path = os.path.normpath(os.path.join(
                            sys.base_exec_prefix, 
                            "Scripts", 
                            "pywin32_postinstall.py"))
                    postinstall_script_path = postinstall_script_path.replace("/", "\\")                    
                    windows_api.RunAsAdmin([
                        sys.executable, 
                        postinstall_script_path])
                            
    
    def run(self):        
        if sys.platform == "win32":
            self._prepare_requirements()
            
        # self.distribution.install_requires
        distutils_install.run(self)
        
        