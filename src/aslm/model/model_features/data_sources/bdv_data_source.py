#  Standard Imports

# Third Party Imports
from decimal import DivisionByZero
import h5py
import numpy as np
import numpy.typing as npt

# Local imports
from .data_source import DataSource
from ..metadata_sources.bdv_metadata import BigDataViewerMetadata

class BigDataViewerDataSource(DataSource):
    def __init__(self, file_name: str = None, mode: str = 'w') -> None:
        super().__init__(file_name, mode)

        self._current_frame = 0
        self.metadata = BigDataViewerMetadata()
        self.image = None
        self._views = None
        self._resolutions = np.array([[1,1,1],[2,2,2],[4,4,4],[8,8,8]],dtype=int)
        self._subdivisions = np.array([[128,128,64],[128,128,64],[128,128,64],[128,128,64]],dtype=int)

    @property
    def resolutions(self) -> npt.ArrayLike:
        return self._resolutions

    @property
    def subdivisons(self) -> npt.ArrayLike:
        return self._subdivisons

    def write(self, data: npt.ArrayLike, **kw) -> None:
        c, z, t = self._czt_indices(self._current_frame, self.metadata.per_stack)
        time_group_name = f"{t:05}"
        setup_group_name = f"{(c*self.shape_z+z):02}"
        for i in range(self.subdivisons.shape[0]):
            dx, dy, dz = self.subdivisons[i,...]
            if z % dz == 0:
                self.image['/'.join([time_group_name, setup_group_name, f"{i}", "cells"])][...,z] = data[::dx, ::dy]
                self._views.append(**kw)
        self._current_frame += 1

    def read(self) -> None:
        self.image = h5py.File(self.file_name, 'r')

    def _setup_h5(self):
        # Create setups
        for i in range(self.shape_c*self.shape_t):
            setup_group_name = f"s{i:02}"
            if setup_group_name in self.image:
                del self.image[setup_group_name]
                self.image.create_dataset(f"{setup_group_name}/resolutions", data=self.resolutions)
                self.image.create_dataset(f"{setup_group_name}/subdivisions", data=self.subdivisons)

        # Create the datasets to populate
        for t in range(self.shape_t):
            for c in range(self.shape_c):
                for z in range(self.shape_z):
                    time_group_name = f"{t:05}"
                    setup_group_name = f"{(c*self.shape_z+z):02}"
                    for i in range(self.subdivisons.shape[0]):
                        dx, dy, dz = self.subdivisons[i,...]
                        self.image.create_dataset('/'.join([time_group_name, setup_group_name, "0", "cells"]),
                                    chunks=tuple(self.resolutions[i,...]),
                                    shape=(self.shape_x//dx , self.shape_y//dy, self.shape_z//dz))

    def _mode_checks(self) -> None:
        self._write_mode = self._mode == 'w'
        self.close()  # if anything was already open, close it
        if self._write_mode:
            self._current_frame = 0
            self.image = h5py.File(self.file_name, 'a')
            self._setup_h5()
        else:
            self.read()

    def close(self) -> None:
        try:
            self.image.close()
            self.metadata.write_xml(self.file_name, views=self._views)
        except AttributeError:
            # image wasn't instantiated, no need to close anything
            pass
