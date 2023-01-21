# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import logging

# Third Party Imports
import numpy.typing as npt

# Local Imports
from multiprocessing.managers import DictProxy


class DataSource:
    def __init__(self, file_name: str = "", mode: str = "w") -> None:
        """
        Base class for data sources, which can be of arbitrary file type.
        This implements read and write methods for accessing each data source.

        We expect to open the file for read or write during initialization.

        file_name  stores the name of the file to read/write from
        data       stores a pointer to the actual data in the data source and
        metdata    stores a pointer to the metadata.

        Concept and some of the code borrowed from python-microscopy
        (https://github.com/python-microscopy/python-microscopy/).

        Parameters
        ----------
        file_name : str
            Name of the file to read/write from.
        mode : str
            Mode to open the file in. Can be 'r' or 'w'.

        Returns
        -------
        None

        Attributes
        ----------
        file_name : str
            Name of the file to read/write from.
        data : npt.ArrayLike
            Pointer to the actual data in the data source.
        metadata : npt.ArrayLike
            Pointer to the metadata.

        """
        self.logger = logging.getLogger(__name__.split(".")[1])
        self.file_name = file_name
        self.metadata = None  # Expect a metadata object
        self._mode = None

        self.dx, self.dy, self.dz = 1, 1, 1  # pixel sizes (um)
        self.dt = 1  # time displacement (s)
        self.dc = 1  # step size between channels, should always be 1
        # shape
        self.shape_x, self.shape_y, self.shape_z, self.shape_t, self.shape_c = (
            1,
            1,
            1,
            1,
            1,
        )
        self.positions = 1
        self.mode = mode

    @property
    def mode(self) -> str:
        """Get the mode of the data source.

        Returns
        -------
        str
            Mode of the data source.

        Examples
        --------
        >>> data_source.mode
        'r'
        """
        return self._mode

    @mode.setter
    def mode(self, mode_str) -> None:
        """Set the mode of the data source.

        Parameters
        ----------
        mode_str : str
            Mode to set the data source to. Can be 'r' or 'w'.

        Returns
        -------
        None

        Examples
        --------
        >>> data_source.mode = 'r'
        """
        if mode_str == self._mode:
            return
        if mode_str in ["r", "w"]:
            self._mode = mode_str
        else:
            self.logger.warning(f"Unknown mode {mode_str}. Setting to 'r'.")
            self._mode = "r"
        self._mode_checks()

    @property
    def data(self) -> npt.ArrayLike:
        """Return array representation of data stored in data source.

        Parameters
        ----------
        None

        Returns
        -------
        npt.ArrayLike
            Array representation of data stored in data source.

        Examples
        --------
        >>> data_source.data
        """
        raise NotImplementedError("Implemented in a derived class.")

    @property
    def voxel_size(self) -> tuple:
        """Return voxel size

        Parameters
        ----------
        None

        Returns
        -------
        tuple
            Voxel size in x, y, z dimensions.

        Examples
        --------
        >>> data_source.voxel_size
        (1, 1, 1)
        """
        return (self.dx, self.dy, self.dz)

    @property
    def shape(self) -> tuple:
        """Return shape as XYCZT.

        Parameters
        ----------
        None

        Returns
        -------
        tuple
            Shape of the data source in XYCZT format.

        Examples
        --------
        >>> data_source.shape
        (1, 1, 1, 1, 1)
        """
        return (self.shape_x, self.shape_y, self.shape_c, self.shape_z, self.shape_t)

    def set_metadata_from_configuration_experiment(
        self, configuration: DictProxy
    ) -> None:
        """Set metadata from configuration experiment.

        Parameters
        ----------
        configuration : DictProxy
            Configuration experiment.

        Returns
        -------
        None

        Examples
        --------
        >>> data_source.set_metadata_from_configuration_experiment(configuration)
        """

        self.metadata.configuration = configuration

        # pull new values from the metadata
        self.dx, self.dy, self.dz = self.metadata.voxel_size
        (
            self.shape_x,
            self.shape_y,
            self.shape_c,
            self.shape_z,
            self.shape_t,
        ) = self.metadata.shape
        self.positions = self.metadata.positions

    def _cztp_indices(self, frame_id: int, per_stack: bool = True) -> tuple:
        """Figure out where we are in the stack from the frame number.

        per_stack indicates if we move through z (per_stack=True) or c fastest.
        we move through positions slower than z or c. we move through time slower than z, c or p.

        Parameters
        ----------
        frame_id : int
            Frame number in the stack.
        per_stack : bool
            Are we acquiring images along z before c? See experiment.yml.

        Returns
        -------
        c : int
            Index of channel
        z : int
            Index of z position
        t : int
            Index of time position
        p : int
            Index of multi-position position.

        Examples
        --------
        >>> data_source._cztp_indices(frame_id)
        (0, 0, 0, 0)
        """
        # If z-stacking, if multi-position
        if self.shape_z > 1:
            # We're z-stacking, make z, c vary faster than t
            if per_stack:
                c = (frame_id // self.shape_z) % self.shape_c
                z = frame_id % self.shape_z
            else:
                c = frame_id % self.shape_c
                z = (frame_id // self.shape_c) % self.shape_z

            t = frame_id // (self.shape_c * self.shape_z * self.positions)
            p = (frame_id // (self.shape_c * self.shape_z)) % self.positions
        else:
            # Timepoint acquisition, only c varies faster than t
            c = frame_id % self.shape_c
            t = (frame_id // self.shape_c) % self.shape_t
            z = (frame_id // (self.shape_c * self.shape_t)) % self.shape_z
            p = (frame_id // (self.shape_c * self.shape_t)) % self.positions

        return c, z, t, p

    def _mode_checks(self) -> None:
        """Run additional checks after setting the mode.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> data_source._mode_checks()"""
        pass

    def write(self, data: npt.ArrayLike, **kw) -> None:
        """Write data to file.

        Parameters
        ----------
        data : npt.ArrayLike
            Data to write to file.
        **kw : dict
            Additional keyword arguments.

        Returns
        -------
        None

        Examples
        --------
        >>> data_source.write(data)
        """
        raise NotImplementedError("Implemented in a derived class.")

    def read(self) -> None:
        """Read data from file.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> data_source.read()"""
        raise NotImplementedError("Implemented in a derived class.")

    def close(self) -> None:
        """Clean up any leftover file pointers, etc.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> data_source.close()"""
        pass

    def __del__(self):
        """Destructor"""
        self.close()
