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
from multiprocessing.managers import DictProxy

# Third-party imports
import numpy as np
import numpy.typing as npt

# Local application imports
from .data_source import DataSource
from ...tools.slicing import ensure_slice, ensure_iter, slice_len


class PyramidalDataSource(DataSource):
    """General class for data sources that store data in a pyramidal structure.

    Implements resolution/subdivision calculations and __getitem__ with
    indexing by subdivision.
    """

    def __init__(self, file_name: str = None, mode: str = "w") -> None:
        """Initializes the PyramidalDataSource.

        Parameters
        ----------
        file_name : str
            The name of the file to write to.
        mode : str
            The mode to open the file in. Must be "w" for write or "r" for read.
        """
        #: np.array: The resolution of each down-sampled pyramid level.
        self._resolutions = np.array(
            [[1, 1, 1], [2, 2, 1], [4, 4, 1], [8, 8, 1]], dtype=int
        )
        #: np.array: The number of subdivisions in each dimension.
        self._subdivisions = None
        #: np.array: The shape of the image.
        self._shapes = None

        super().__init__(file_name, mode)

    @property
    def resolutions(self) -> npt.ArrayLike:
        """Getter for resolutions.

        Store as XYZ per BDV spec.

        Returns
        -------
        resolutions : npt.ArrayLike
            The resolutions.
        """
        return self._resolutions

    @property
    def subdivisions(self) -> npt.ArrayLike:
        """Getter for subdivisions.

        Store as XYZ per BDV spec.

        Returns
        -------
        subdivisions : npt.ArrayLike
            The subdivisions.
        """
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
        """Getter for image shape.

        Store as ZYX rather than XYZ, per BDV spec.

        Returns
        -------
        shapes : npt.ArrayLike
            The shapes.
        """
        if self._shapes is None:
            self._shapes = np.maximum(
                np.ceil(
                    np.array([self.shape_z, self.shape_y, self.shape_x])[None, :]
                    / self.resolutions[:, ::-1]
                ).astype(int),
                1,
            )
        return self._shapes

    @property
    def nbytes(self) -> int:
        """Getter for image size.

        Size in bytes. Overrides base class. Accounts for subdivisions.

        Returns
        -------
        size : int
            The size of the image in bytes.
        """
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
        """Sets the metadata from according to the microscope configuration.

        Parameters
        ----------
        configuration : DictProxy
            The configuration experiment.
        """
        self._subdivisions = None
        self._shapes = None

        return super().set_metadata_from_configuration_experiment(configuration)

    def __getitem__(self, keys):
        """Magic method to get slice requests passed by, e.g., ds[:,2:3,...].
        Allows arbitrary slicing of dataset via calls to get_slice().

        Order is xycztps where x, y, z are array indices, c is channel,
        t is timepoints, p is positions and s is subdivisions to index along.

        TODO: Add subdivisions.

        Parameters
        ----------
        keys : tuple
            Tuple of indices.

        Returns
        -------
        npt.ArrayLike
            Array of shape (p, t, z, c, y, x)
        """

        # Check lengths
        if isinstance(keys, slice) or isinstance(keys, int):
            length = 1
        else:
            length = len(keys)

        if length < 1:
            raise IndexError(
                "Too few indices. Indices may be (x, y, c, z, t, p, subdiv)."
            )
        elif length > 7:
            raise IndexError(
                "Too many indices. Indices may be (x, y, c, z, t, p, subdiv)."
            )

        # Get indices as slices/ranges
        xs = ensure_slice(keys, 0)
        ys = ensure_slice(keys, 1)
        cs = ensure_iter(keys, 2, self.shape[2])
        zs = ensure_slice(keys, 3)
        ts = ensure_iter(keys, 4, self.shape[4])
        ps = ensure_iter(keys, 5, self.positions)

        if length > 1 and keys[-1] == Ellipsis:
            keys = keys[:-1]
            length -= 1

        if length > 6 and isinstance(keys[6], int):
            subdiv = keys[6]
        else:
            subdiv = 0

        if len(cs) == 1 and len(ts) == 1 and len(ps) == 1:
            return self.get_slice(xs, ys, cs[0], zs, ts[0], ps[0], subdiv)

        sliced_ds = np.empty(
            (
                len(ps),
                len(ts),
                slice_len(zs, self.shape_z) // self.resolutions[subdiv][2],
                len(cs),
                slice_len(ys, self.shape_y) // self.resolutions[subdiv][1],
                slice_len(xs, self.shape_x) // self.resolutions[subdiv][0],
            ),
            dtype=self.dtype,
        )

        for c in cs:
            for t in ts:
                for p in ps:
                    sliced_ds[p, t, :, c, :, :] = self.get_slice(
                        xs, ys, c, zs, t, p, subdiv
                    )

        return sliced_ds

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

        Raises
        ------
        NotImplementedError
            If the method is not implemented in a derived class.
        """
        raise NotImplementedError("Implemented in a derived class.")
