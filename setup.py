from gettext import install
from setuptools import setup

with open('requirements.txt', 'r') as fp:
    install_requires = list(fp.read().splitlines())

setup(
     name='aslm',
     version='0.0.1',
     package_dir = {"": "src"},
     entry_points={
         'console_scripts': [
             'aslm = aslm.main:main',
         ]
     },
     include_package_data=True,
     install_requires=install_requires
 ) 

