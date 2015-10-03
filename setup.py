from setuptools import setup, find_packages
setup(
  name = "rime_plus",
  version = "0.9.0",
  scripts          = ['bin/rime', 'bin/rime_init'],
  packages         = find_packages(),
  package_dir      = {'rime': 'rime'},
)
