#!/usr/bin/env python

import os
import os.path
import sys
import shutil
import logging
import fnmatch
import src as rabird
from setuptools import setup, find_packages

from_package = 'src'
to_package = 'rabird'

def convert_source_for_version(source_package, destination_package, version):
	tag_line = r'#--IMPORT_ALL_FROM_FUTURE--#'
	
	shutil.rmtree(destination_package,  ignore_errors=True)
	shutil.copytree(source_package, destination_package)
	
	if version != 2:
		# We wrote program implicated by version 3, if python version large than 2,
		# we need not change the sources.
		return
		
	for root, dirs, files in os.walk(destination_package):
		for afile in files:
			if fnmatch.fnmatch(afile, '*.py') or fnmatch.fnmatch(afile, '*.pyw'):
				file_path = os.path.join(root, afile)
				source_file = open(file_path, 'rb+')
				content = source_file.read()
				founded_index = content.find(tag_line)
				if founded_index >= 0:
					source_file.seek(0) # Go to beginning of file ...
					source_file.write(content[0:founded_index]) # All things before tag line
					# Import all future stuffs while we are using python 2.7.x
					source_file.write('from __future__ import nested_scopes\n')
					source_file.write('from __future__ import generators\n')
					source_file.write('from __future__ import division\n')
					source_file.write('from __future__ import absolute_import\n')
					source_file.write('from __future__ import with_statement\n')
					source_file.write('from __future__ import print_function\n')
					source_file.write('from __future__ import unicode_literals\n')
					source_file.write(content[founded_index+len(tag_line):]) # Rest after tag line
				source_file.close()

logging.basicConfig(level=logging.INFO)

source_version_file_path = 'source_version.txt'
source_version_file = None
if os.path.exists(source_version_file_path):
	source_version_file = open(source_version_file_path, 'rb+')
	version = int(source_version_file.read())
	if version != sys.version_info.major:
		source_version_file.seek(0)
		source_version_file.write(str(sys.version_info.major).encode('utf-8'))
		convert_source_for_version(from_package, to_package, sys.version_info.major)	
else:
	source_version_file = open(source_version_file_path, 'wb')
	source_version_file.write(str(sys.version_info.major).encode('utf-8'))
	convert_source_for_version(from_package, to_package, sys.version_info.major)
source_version_file.close()

# Exclude the original source package, only accept the preprocessed package!
pkgs = find_packages(exclude=[from_package]) 

setup(
	name=to_package,
	version=rabird.__version__,
	author='HongShe Liang',
	author_email='starofrainnight@gmail.com',
	url='',
	py_modules=[to_package],
	description='{} utilities'.format(to_package),
	long_description=open('README', 'r').read(),
	classifiers=[
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 3',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: BSD License',
		'Topic :: Software Development :: Libraries',
		'Topic :: Utilities',
	],
    packages = pkgs,
	)

