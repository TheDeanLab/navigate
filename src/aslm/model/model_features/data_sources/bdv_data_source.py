#  Standard Imports

# Third Party Imports
import h5py

# Local imports
from .data_source import DataSource

class BigDataViewerDataSource(DataSource):
    def __init__(self, file_name: str = None, mode: str = 'w') -> None:
        super().__init__(file_name, mode)

    