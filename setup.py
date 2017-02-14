from setuptools import setup, find_packages
import sys


if sys.version_info[0] == 2:
  setup(
    name = "rime_plus",
    version = "1.0.0",
    scripts          = ['bin/rime', 'bin/rime_init'],
    packages         = find_packages(),
    package_dir      = {'rime': 'rime'},
  )
else:
  print("rime-plus support only python2.")
  print("please use:")
  print("    python2 -m pip install git+https://github.com/icpc-jag/rime-plus")
  sys.exit(1)
