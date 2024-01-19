import os
from pathlib import Path

from ._commit import __commit__  # noqa: F401

with open(os.path.join(Path(__file__).resolve().parent, 'VERSION')) as version_file:
    __version__ = version_file.read().strip()
    