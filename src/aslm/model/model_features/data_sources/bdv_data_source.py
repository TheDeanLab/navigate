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
        c, z, t = self._czt_indices(self._current_frame, self.metadata.per_stack)
        time_group_name = f"{t:05}"
        setup_group_name = f"{(c*self.shape_z+z):02}"
        self.image.create_dataset('/'.join([time_group_name, setup_group_name, "0", "cells"]),
                                  shape=(self.shape_x, self.shape_y), data=data)

    def read(self) -> None:
        self.image = h5py.File(self.file_name, 'r')

    def _setup_h5(self):
        for i in range(self.metadata.setups):
            setup_group_name = f"s{i:02}"
            if setup_group_name in self.image:
                del self.image[setup_group_name]
            self.image.create_group(setup_group_name+"/0")

    def _mode_checks(self) -> None:
        self._write_mode = self._mode == 'w'
        self.close()  # if anything was already open, close it
        if self._write_mode:
            self.image = h5py.File(self.file_name, 'a')
            self._setup_h5()
        else:
            self.read()

    def close(self) -> None:
        try:
            self.image.close()
        except AttributeError:
            # image wasn't instantiated, no need to close anything
            pass
