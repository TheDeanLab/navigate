# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

# Standard library imports

# Third-party imports
import zarr
import numpy.typing as npt
import zarr.storage

# Local application imports
from .pyramidal_data_source import PyramidalDataSource
from ..metadata_sources.zarr_metadata import OMEZarrMetadata

GROUP_PREFIX = "p"


class OMEZarrDataSource(PyramidalDataSource):
    """OME-Zarr data source.

    This class implements an OME-Zarr image data source using the Zarr v2 format.
    """

    def __init__(self, file_name: str = None, mode: str = "w") -> None:

        #: OMEZarrMetadata: Metadata object for the OME-Zarr data source.
        self.metadata = OMEZarrMetadata()
        self.__store = None
        self._current_position = -1

        super().__init__(file_name, mode)

    def get_slice(self, x, y, c, z=0, t=0, p=0, subdiv=0) -> npt.ArrayLike:
        """Get a 3D slice of the dataset for a single c, t, p, subdiv.

        Parameters
        ----------
        x : int or slice
            x indices to grab
        y : int or slice
            y indices to grab
        c : int
            Single channel
        z : int or slice
            z indices to grab
        t : int
            Single timepoint
        p : int
            Single position
        subdiv : int
            Subdivision of the dataset to index along

        Returns
        -------
        npt.ArrayLike
            3D (z, y, x) slice of data set
        """
        dataset_name = f"{GROUP_PREFIX}{p}_{subdiv}"
        return self.image[dataset_name][t, c, z, y, x]

    def setup(self):
        """Set up the Zarr writer."""
        # Use FSStore as a universal backend
        self.__store = zarr.storage.FSStore(self.file_name, mode=self.mode)

        #: zarr.group: Zarr group object for the image data source.
        self.image = zarr.group(store=self.__store, overwrite=True)
        self._current_position = -1

    def new_position(self, pos, view):
        """Create new arrays on the fly for each position in self.positions.

        Parameters
        ----------
        pos : int
            Position index
        view : str
            View name
        """
        name = f"{GROUP_PREFIX}{pos}"
        paths = []
        # Create the subdivisions...
        for si, zyx_shape in enumerate(self.shapes):
            shape = tuple([self.shape_t, self.shape_c] + list(zyx_shape))
            setup = f"{name}_{si}"
            arr = self.image.create(
                name=setup,
                shape=shape,
                chunks=(1,) * len(shape[:-2]) + shape[-2:],
                dtype=self.dtype,
            )
            # xarray multidim
            paths.append(arr.path)
            arr.attrs["_ARRAY_DIMENSIONS"] = shape

        # Append setup to multiscales
        scales = self.image.attrs.get("multiscales", [])
        scales.append(
            self.metadata.multiscales_dict(name, paths, self.resolutions, view)
        )
        self.image.attrs["multiscales"] = scales

    def write(self, data: npt.ArrayLike, **kw) -> None:
        """Writes 2D image to the data source.

        Parameters
        ----------
        data : npt.ArrayLike
            2D image data
        kw : dict
            Keyword arguments
        """
        #: str: Mode of the data source.
        self.mode = "w"

        if self.__store is None:
            self.setup()

        c, z, t, p = self._cztp_indices(
            self._current_frame, self.metadata.per_stack
        )  # find current channel

        if self._current_position != p:
            self._current_position = p
            if len(kw) > 0:
                self.new_position(p, kw)
            else:
                self.new_position(p)

        for ri, res in enumerate(self.resolutions):
            dx, dy, dz = res
            dataset_name = f"{GROUP_PREFIX}{p}_{ri}"
            zs = min(z // dz, self.shapes[ri, 0] - 1)
            self.image[dataset_name][t, c, zs, ...] = data[::dy, ::dx].astype(
                self.dtype
            )

        self._current_frame += 1

    def read(self) -> None:
        """Reads data from the image file."""
        self.mode = "r"
        self.__store = zarr.storage.FSStore(self.file_name, mode=self.mode)
        self.image = zarr.group(store=self.__store)
        # TODO: parse the image metadata
        self.get_shape_from_metadata()

    def close(self) -> None:
        """Close the image file."""
        if self._closed:
            if self.__store is not None:
                self.__store = None
            return
        self._check_shape(self._current_frame - 1, self.metadata.per_stack)
        self.__store.close()
        self._closed = True
        self.__store = None
