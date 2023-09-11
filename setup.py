import os
import setuptools


def get_long_description() -> str:
    readme = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme) as f:
        return f.read()


setuptools.setup(
    name='rime',
    version='2.1.0',
    description="An automation tool for programming contest organizers",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    scripts=['bin/rime', 'bin/rime_init'],
    packages=['rime', 'rime.basic', 'rime.basic.targets', 'rime.basic.util',
              'rime.core', 'rime.plugins', 'rime.plugins.judge_system',
              'rime.plugins.plus', 'rime.plugins.summary', 'rime.util'],
    package_dir={'rime': 'rime'},
    install_requires=['six', 'Jinja2', 'requests'],
    tests_require=['pytest', 'mock'],
    package_data={'rime': ['plugins/summary/*.ninja']},
)
