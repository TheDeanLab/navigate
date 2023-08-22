# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

#  Standard Imports
import os

# Third Party Imports
import h5py
import zarr  # for n5
import numpy as np
import numpy.typing as npt

# Local imports
from .data_source import DataSource
from ..metadata_sources.bdv_metadata import BigDataViewerMetadata
from multiprocessing.managers import DictProxy


class BigDataViewerDataSource(DataSource):
    def __init__(self, file_name: str = None, mode: str = "w") -> None:
        self._resolutions = np.array(
            [[1, 1, 1], [2, 2, 1], [4, 4, 1], [8, 8, 1]], dtype=int
        )
        self._subdivisions = None
        self._shapes = None
        self.image = None
        self._views = []
        self.__store = None

        self.__file_type = os.path.splitext(os.path.basename(file_name))[-1][1:].lower()
        if self.__file_type not in ["h5", "n5"]:
            raise ValueError(f"Unknown file type {self.__file_type}.")
        if self.__file_type == "h5":
            self.setup = self._setup_h5
            self.ds_name = self._h5_ds_name
        elif self.__file_type == "n5":
            self.setup = self._setup_n5
            self.ds_name = self._n5_ds_name
        super().__init__(file_name, mode)

        # self._current_frame = 0
        self.metadata = BigDataViewerMetadata()

    @property
    def resolutions(self) -> npt.ArrayLike:
        """Store as XYZ per BDV spec."""
        return self._resolutions

    @property
    def subdivisions(self) -> npt.ArrayLike:
        """Store as XYZ per BDV spec."""
        if self._subdivisions is None:
            self._subdivisions = np.zeros((4, 3), dtype=int)
            self._subdivisions[:, 0] = np.gcd(32, self.shapes[:, 0])
            self._subdivisions[:, 1] = np.gcd(32, self.shapes[:, 1])
            self._subdivisions[:, 2] = np.gcd(32, self.shapes[:, 2])

            # Safety
            self._subdivisions = np.maximum(self._subdivisions, 1)

            # Reverse to XYZ
            self._subdivisions = self._subdivisions[:, ::-1]
        return self._subdivisions

    @property
    def shapes(self) -> npt.ArrayLike:
        """Store as ZYX rather than XYZ, per BDV spec."""
        if self._shapes is None:
            self._shapes = np.maximum(
                np.array([self.shape_z, self.shape_y, self.shape_x])[None, :]
                // self.resolutions[:, ::-1],
                1,
            )
        return self._shapes

    @property
    def size(self) -> int:
        """Size in bytes. Overrides base class."""
        return (
            np.prod(self.shapes, axis=1)
            * self.shape_t
            * self.shape_c
            * self.positions
            * self.bits
            // 8
        ).sum()

    def set_metadata_from_configuration_experiment(
        self, configuration: DictProxy
    ) -> None:
        self._subdivisions = None
        self._shapes = None
        return super().set_metadata_from_configuration_experiment(configuration)

    def write(self, data: npt.ArrayLike, **kw) -> None:
        self.mode = "w"

        is_kw = len(kw) > 0

        c, z, t, p = self._cztp_indices(
            self._current_frame, self.metadata.per_stack
        )  # find current channel

        if not (z or c or t or p):
            self.setup()

        ds_name = self.ds_name(t, c, p)
        for i in range(self.subdivisions.shape[0]):
            dx, dy, dz = self.resolutions[i, ...]
            if z % dz == 0:
                dataset_name = ds_name.replace("???", str(i))
                # print(z, dz, dataset_name, self.image[dataset_name].shape,
                #       data[::dx, ::dy].shape)
                zs = min(z // dz, self.shapes[i, 0] - 1)  # TODO: Is this necessary?
                self.image[dataset_name][zs, ...] = data[::dy, ::dx]
                if is_kw and (i == 0):
                    self._views.append(kw)
        self._current_frame += 1

        # Check if this was the last frame to write
        c, z, t, p = self._cztp_indices(self._current_frame, self.metadata.per_stack)
        if (z == 0) and (c == 0) and ((t >= self.shape_t) or (p >= self.positions)):
            self.close()

    def _h5_ds_name(self, t, c, p):
        time_group_name = f"t{t:05}"
        setup_group_name = f"s{(c*self.positions+p):02}"
        ds_name = "/".join([time_group_name, setup_group_name, "???", "cells"])
        return ds_name

    def _n5_ds_name(self, t, c, p):
        time_group_name = f"timepoint{t}"
        setup_group_name = f"setup{(c*self.positions+p)}"
        ds_name = "/".join([setup_group_name, time_group_name, "s???"])
        return ds_name

    def read(self) -> None:
        self.mode = "r"
        if self.__file_type == "h5":
            self.image = h5py.File(self.file_name, "r")
        elif self.__file_type == "n5":
            self.image = zarr.N5Store(self.file_name)

    def _setup_h5(self):
        self.image = h5py.File(self.file_name, "a")

        # Create setups
        for i in range(self.shape_c * self.positions):
            setup_group_name = f"s{i:02}"
            if setup_group_name in self.image:
                del self.image[setup_group_name]
            self.image.create_dataset(
                f"{setup_group_name}/resolutions", data=self.resolutions
            )
            self.image.create_dataset(
                f"{setup_group_name}/subdivisions", data=self.subdivisions
            )

        # Create the datasets to populate
        for t in range(self.shape_t):
            time_group_name = f"t{t:05}"
            for i in range(self.shape_c * self.positions):
                setup_group_name = f"s{i:02}"
                for j in range(self.subdivisions.shape[0]):
                    dataset_name = "/".join(
                        [time_group_name, setup_group_name, f"{j}", "cells"]
                    )
                    if dataset_name in self.image:
                        del self.image[dataset_name]
                    # print(f"Creating {dataset_name} with shape {self.shapes[j,...]}")
                    self.image.create_dataset(
                        dataset_name,
                        chunks=tuple(self.subdivisions[j, ...][::-1]),
                        shape=self.shapes[j, ...],
                        dtype="uint16",
                    )

    def _setup_n5(self):
        self.__store = zarr.N5Store(self.file_name)
        self.image = zarr.group(store=self.__store, overwrite=True)

        # Note that setups and timepoints are flipped in N5 vs. HDF5, see
        # https://github.com/bigdataviewer/bigdataviewer-core/blob/master/BDV%20N5%20format.md
        for i in range(self.shape_c * self.positions):
            setup_group_name = f"setup{i}"
            setup = self.image.create_group(setup_group_name)
            setup.attrs["downsamplingFactors"] = self.resolutions.tolist()
            setup.attrs["dataType"] = "uint16"
            for t in range(self.shape_t):
                time_group_name = f"timepoint{t}"
                timepoint = setup.create_group(time_group_name)
                for j in range(self.subdivisions.shape[0]):
                    s_group_name = f"s{j}"
                    shape = self.shapes[j, ...][::-1]
                    # chunks = self.subdivisions[j, ...]
                    sx = timepoint.zeros(
                        s_group_name, shape=tuple(shape), chunks=(shape[0], shape[1], 1)
                    )
                    sx.attrs["dataType"] = "uint16"
                    sx.attrs["blockSize"] = [shape[0], shape[1], 1]
                    sx.attrs["dimensions"] = list(shape)
        # print(self.image.tree())

    def _mode_checks(self) -> None:
        self._write_mode = self._mode == "w"
        self.close()  # if anything was already open, close it
        if self._write_mode:
            self._current_frame = 0
            self._views = []
            self.setup()
        else:
            self.read()
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._check_shape(self._current_frame - 1, self.metadata.per_stack)
        # print(
        #     f"Post-check current_frame: {self._current_frame-1} x: {self.shape_x}"
        #     f" y: {self.shape_y} z: {self.shape_z} c: {self.shape_c} "
        #     f"t: {self.shape_t} p: {self.positions}"
        # )
        if self.__file_type == "n5":
            self.__store.close()
        else:
            self.image.close()
        self.metadata.write_xml(self.file_name, views=self._views)
        self._closed = True
