from distutils.core import setup
import py2exe
import sys
import os

sys.argv.append('py2exe')
sys.argv.append('-q')

setup(
  options = {'py2exe': {'bundle_files': 1}},
  zipfile = None,
  console = [{'script': 'randy.py'}]
)
