import setuptools

setuptools.setup(
    name='rime',
    version='3.0.0.dev',
    scripts=['bin/rime', 'bin/rime_init'],
    packages=['rime', 'rime.basic', 'rime.basic.targets', 'rime.basic.util',
              'rime.core', 'rime.plugins', 'rime.plugins.judge_system',
              'rime.plugins.plus', 'rime.plugins.summary', 'rime.util'],
    package_dir={'rime': 'rime'},
    install_requires=['six', 'Jinja2', 'requests'],
    tests_require=['pytest', 'mock'],
    package_data={'rime': ['plugins/summary/*.ninja']},
)
