from setuptools import setup, find_packages
setup(
  name = "rime",
  version = "1.0",
  scripts          = ['bin/rime'],
  packages         = find_packages(),
  package_dir      = {'rime': 'rime'},
)
