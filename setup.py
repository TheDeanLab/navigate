import os
import re
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "src", "aslm", "_version.py")) as f:
    match = re.search(r"^__version__\s?=\s?['\"]([^'\"]*)['\"]", f.read())
    if match:
        VERSION = match.groups()[0]

with open('requirements.txt', 'r') as fp:
    install_requires = list(fp.read().splitlines())

print(VERSION)

setup(
     name='aslm',
     version=VERSION,
     package_dir={"": "src"},
     entry_points={
         'console_scripts': [
             'aslm = aslm.main:main',
         ]
     },
     include_package_data=True,
     install_requires=install_requires
 ) 

