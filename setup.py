import setuptools
import sys

mox = 'mox' if sys.version_info[0] == 2 else 'mox3'

setuptools.setup(
    name='rime',
    version='2.0.dev1',
    scripts=['bin/rime', 'bin/rime_init'],
    packages=['rime', 'rime.basic', 'rime.basic.targets', 'rime.basic.util',
              'rime.core', 'rime.plugins', 'rime.plugins.judge_system',
              'rime.plugins.plus', 'rime.util'],
    package_dir={'rime': 'rime'},
    install_requires=['six'],
    test_suite='nose.collector',
    tests_require=['nose', mox],
)
