from setuptools import setup, find_packages
import os
import re

_readme = 'README.md'
_extras = 'extras'

with open(_readme, 'r', encoding='utf-8') as f:
    _long_description = f.read()

with open(os.path.join(_extras, '.env'), 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('PACKAGE='):
            _package = line.splitlines()[0].split('=')[1].lower()
        if line.startswith('URL='):
            _url = line.splitlines()[0].split('=')[1].lower()
        if line.startswith('AUTHORS='):
            _authors = line.splitlines()[0].split('=')[1].lower()
        if line.startswith('DESCR='):
            _descr = line.splitlines()[0].split('=')[1].lower()
        if line.startswith('CORR_AUTHOR='):
            _corr_author = line.splitlines()[0].split('=')[1].lower()

with open(os.path.join(_package, '_version.py'), 'r') as ifh:
    for line in ifh:
        m = re.search('__version__.*=.*"(.+)"', line)
        if m:
            _version = m.group(1)
            break

setup(
    name='rpviz',
    version=_version,
    description='Visualize pathways from the RetroPath Suite.',
    license='MIT',
    author='Thomas Duigou, Melchior du Lac',
    author_email='thomas.duigou@inrae.fr',
    packages=find_packages(),
    include_package_data=True,
    keywords=['rpviz'],
    url='https://github.com/brsynth/rpviz',
    classifiers=[
        'Topic :: Scientific/Engineering',
    ]
)