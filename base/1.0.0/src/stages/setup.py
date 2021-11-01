from setuptools import find_namespace_packages
from setuptools import setup
from distutils.log import warn
from setuptools.command.upload import upload as OrigUploader
class FakeUploader(OrigUploader):
    description = "Fake uploader telling you uploading is forbidden"
    user_options = []
    def initialize_options(self):
        pass
    def run(self):
        warn("You are not allowed to upload this package")
setup(
    name="smaract.ctl",
    version="1.3.13",
    packages=find_namespace_packages(include=["smaract.ctl"]),
    description="SmarActCTL Python API",
    url="https://www.smaract.com",
    maintainer="SmarAct GmbH",
    maintainer_email="info@smaract.com",
    install_requires=("cffi"),
    setup_requires=("setuptools >= 40.1.0"),
    license="SmarAct EULA",
    entry_points = {"distutils.commands": ["upload = FakeUploader"]}
)
