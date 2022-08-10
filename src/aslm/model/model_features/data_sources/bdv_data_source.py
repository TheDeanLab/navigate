#  Standard Imports

# Third Party Imports
import h5py
import numpy.typing as npt

# Local imports
from .data_source import DataSource
from ..metadata_sources.bdv_metadata import BigDataViewerMetadata

class BigDataViewerDataSource(DataSource):
    def __init__(self, file_name: str = None, mode: str = 'w') -> None:
        super().__init__(file_name, mode)

        self.metadata = BigDataViewerMetadata()
        self.image = None

    def write(self, data: npt.ArrayLike, **kw) -> None:
        pass

    def read(self) -> None:
        self.image = h5py.File(self.file_name, 'r')

    def _mode_checks(self) -> None:
        self._write_mode = self._mode == 'w'
        self.close()  # if anything was already open, close it
        if self._write_mode:
            self.image = h5py.File(self.file_name, 'w')
        else:
            self.read()

    def close(self) -> None:
        try:
            self.image.close()
        except AttributeError:
            # image wasn't instantiated, no need to close anything
            pass
