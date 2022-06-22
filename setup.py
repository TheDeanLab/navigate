from setuptools import setup, find_packages, find_namespace_packages

setup(
     name='aslm',
     version='1.0.0',
     package_dir = {"": "src"},
     entry_points={
         'console_scripts': [
             'aslm = aslm.main:main',
         ]
     },
     include_package_data=True,
     python_requires='==3.9.7'
 ) 