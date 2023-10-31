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

        Attributes
        ----------
        logger : logging.Logger
            Logger for this class.
        file_name : str
            Name of the file to read/write from.
        metadata : npt.ArrayLike
            Pointer to the metadata.
        bits : int
            Number of bits per pixel.
        dx : float
            Pixel size in x dimension (microns).
        dy : float
            Pixel size in y dimension (microns).
        dz : float
            Pixel size in z dimension (microns).
        dt : float
            Time displacement (seconds).
        dc : float
            Step size between channels (always 1)
        shape_x : int
            Size of the data source in x dimension.
        shape_y : int
            Size of the data source in y dimension.
        shape_z : int
            Size of the data source in z dimension.
        shape_t : int
            Size of the data source in t dimension.
        shape_c : int
            Size of the data source in c dimension.
        positions : int
            Number of positions in the data source.
        mode : str
            Mode to open the file in. Can be 'r' or 'w'.

        Methods
        -------
        nbytes()
            Return the size of the data source in bytes.
        mode()
            Return the mode of the data source.
        voxel_size()
            Return the voxel size in x, y, z dimensions.
        shape()
            Return the shape of the data source in XYCZT format.
        set_metadata_from_configuration_experiment(configuration)
            Set the metadata from the microscope configuration.
        read()
            Read data from file.
        write(data, **kw)
            Write data to file.
        close()
            Clean up any leftover file pointers, etc.

        """
        self.logger = logging.getLogger(__name__.split(".")[1])
        self.file_name = file_name
        if not hasattr(self, "metadata"):
            self.metadata = None  # Expect a metadata object
        self._mode = None
        self._closed = True
        self.bits = 16

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
        self._current_frame = 0

    @property
    def nbytes(self) -> int:
        """Getter for the size of this data source in bytes."

        Does not account for pyramidal data sources.
        """
        total_bits = (
            self.shape_x
            * self.shape_y
            * self.shape_z
            * self.shape_t
            * self.shape_c
            * self.positions
            * self.bits
        )
        total_bytes = total_bits // 8
        return total_bytes

    @property
    def mode(self) -> str:
        """Getter for the mode of the data source.

        Returns
        -------
        str
            Mode of the data source.
        """
        return self._mode

    @mode.setter
    def mode(self, mode_str) -> None:
        """Setter for the mode of the data source.

        Parameters
        ----------
        mode_str : str
            Mode to set the data source to. Can be 'r' or 'w'.

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



        Returns
        -------
        npt.ArrayLike
            Array representation of data stored in data source.

        Raises
        ------
        NotImplementedError
            If not implemented in a derived class.

        """
        raise NotImplementedError("Implemented in a derived class.")

    @property
    def voxel_size(self) -> tuple:
        """Getter for the voxel size

        Returns
        -------
        tuple
            Voxel size in x, y, z dimensions.

        """
        return (self.dx, self.dy, self.dz)

    @property
    def shape(self) -> tuple:
        """Getter for the shape as XYCZT.

        Returns
        -------
        tuple
            Shape of the data source in XYCZT format.

        """
        return (self.shape_x, self.shape_y, self.shape_c, self.shape_z, self.shape_t)

    def set_metadata_from_configuration_experiment(
        self, configuration: DictProxy
    ) -> None:
        """Sets the metadata from according to the microscope configuration.

        Parameters
        ----------
        configuration : DictProxy
            Configuration experiment.

        """

        self.metadata.configuration = configuration
        self.get_shape_from_metadata()

    def get_shape_from_metadata(self):
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
        we move through positions slower than z or c. we move through time slower
        than z, c or p.

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

            t = (frame_id // (self.shape_c * self.shape_z)) % self.shape_t
            p = frame_id // (self.shape_c * self.shape_z * self.shape_t)

            # NOTE: Uncomment this if we want positions to vary faster than time
            # t = frame_id // (self.shape_c * self.shape_z * self.positions)
            # p = (frame_id // (self.shape_c * self.shape_z)) % self.positions

        else:
            # Timepoint acquisition, only c varies faster than t
            c = frame_id % self.shape_c
            t = (frame_id // self.shape_c) % self.shape_t
            z = (frame_id // (self.shape_c * self.shape_t)) % self.shape_z
            p = frame_id // (self.shape_c * self.shape_t * self.shape_z)

        return c, z, t, p

    def _check_shape(self, max_frame: int = 0, per_stack: bool = True):
        # Check if we've closed this prior to completion
        c, z, t, p = self._cztp_indices(max_frame, per_stack)
        # print(f"max_frame: {max_frame} c: {c} z: {z} t: {t} p: {p}")
        # print(f"XYCZTP: {self.shape} {self.positions}")
        if (
            (z < (self.shape_z - 1))
            or (c < (self.shape_c - 1))
            or (t < (self.shape_t - 1))
            or (p < (self.positions - 1))
        ):
            # If we have, update our shape accordingly
            maxc, maxz, maxt, maxp = 0, 0, 0, 0
            for idx in range(max_frame + 1):
                c, z, t, p = self._cztp_indices(idx, per_stack)
                maxc = max(maxc, c)
                maxz = max(maxz, z)
                maxt = max(maxt, t)
                maxp = max(maxp, p)
            self.shape_c, self.shape_z = maxc + 1, maxz + 1
            self.shape_t, self.positions = maxt + 1, maxp + 1
            if self.metadata is not None:
                self.metadata.shape_c, self.metadata.shape_z = maxc + 1, maxz + 1
                self.metadata.shape_t, self.metadata.positions = maxt + 1, maxp + 1
        # print(
        #     f"result c: {self.shape_c} z: {self.shape_z} "
        #     f"t: {self.shape_t} p: {self.positions}"
        # )

    def _mode_checks(self) -> None:
        """Run additional checks after setting the mode."""
        pass

    def write(self, data: npt.ArrayLike, **kw) -> None:
        """Write data to file.

        Parameters
        ----------
        data : npt.ArrayLike
            Data to write to file.
        **kw : dict
            Additional keyword arguments.

        Raises
        ------
        NotImplementedError
            If not implemented in a derived class.

        """
        raise NotImplementedError("Implemented in a derived class.")

    def read(self) -> None:
        """Read data from file.

        Raises
        ------
        NotImplementedError
            If not implemented in a derived class.

        """
        raise NotImplementedError("Implemented in a derived class.")

    def close(self) -> None:
        """Clean up any leftover file pointers, etc."""
        pass

    def __del__(self):
        """Destructor"""
        if not self._closed:
            self.close()
