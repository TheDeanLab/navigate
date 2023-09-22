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

#  Standard Imports
import os
import uuid
from pathlib import Path

# Third Party Imports
import tifffile
import numpy.typing as npt

# Local imports
from .data_source import DataSource
from ..metadata_sources.metadata import Metadata
from ..metadata_sources.ome_tiff_metadata import OMETIFFMetadata


class TiffDataSource(DataSource):
    """Data source for TIFF files.

    Parameters
    ----------
    file_name : str
        Path to file.
    mode : str
        File mode. "r" for read, "w" for write.
    is_bigtiff : bool
        Is this a bigtiff file?

    Attributes
    ----------
    image : tifffile.TiffFile
        Tiff file object.
    metadata : Metadata
        Metadata object.
    save_directory : str
        Directory to save files to.

    Methods
    -------
    read()
        Read data from file.
    write(data, **kw)
        Write data to file.
    generate_image_name(current_channel, current_time_point)
        Generate a string for the filename.
    close
        Close the file.

    """

    def __init__(
        self, file_name: str = "", mode: str = "w", is_bigtiff: bool = False
    ) -> None:
        self.image = None
        self._write_mode = None
        self._views = []

        super().__init__(file_name, mode)

        self.save_directory = Path(self.file_name).parent

        # Is this an OME-TIFF?
        # TODO: check the header, rather than use the file extension
        if self.file_name.endswith(".ome.tiff") or self.file_name.endswith(".ome.tif"):
            self._is_ome = True
            self.metadata = OMETIFFMetadata()
        else:
            self._is_ome = False
            self.metadata = Metadata()

        self._is_bigtiff = is_bigtiff

        # For file writing, do we assume all files end with tiff or tif?
        self.__double_f = self.file_name.endswith("tiff")

        # Keep track of z, time, channel indices
        # self._current_frame = 0
        self._current_time = 0
        self._current_position = 0

    @property
    def data(self) -> npt.ArrayLike:
        self.mode = "r"

        return self.image.asarray()

    @property
    def is_bigtiff(self) -> bool:
        if self._write_mode:
            return self._is_bigtiff
        else:
            return self.image.is_bigtiff

    def set_bigtiff(self, is_bigtiff: bool) -> None:
        self._is_bigtiff = is_bigtiff

    @property
    def is_ome(self) -> bool:
        if self._write_mode:
            return self._is_ome
        else:
            return self.image.is_ome

    def read(self) -> None:
        self.image = tifffile.TiffFile(self.file_name)

        # TODO: Parse metadata
        for i, ax in enumerate(list(self.image.series[0].axes)):
            if ax == "Q":
                # TODO: This is a hack for tifffile. Find a way to remove this.
                ax = "Z"
            setattr(self, f"shape_{ax.lower()}", self.data.shape[i])

    def write(self, data: npt.ArrayLike, **kw) -> None:
        """Write data to a tiff file.

        One channel, all z-position, one timepoint = one stack.
        N channels are opened simultaneously for writing.
        At each time point, a new file is opened for each channel.

        Parameters
        ----------
        data : npt.ArrayLike
            Data to write to file.
        kw : dict
            Keyword arguments to pass to tifffile.imsave.

        Returns
        -------
        None
        """
        self.mode = "w"

        c, z, self._current_time, self._current_position = self._cztp_indices(
            self._current_frame, self.metadata.per_stack
        )  # find current channel
        if z == 0:
            if c == 0:
                # Make sure we're set up for writing
                self._setup_write_image()
            if self.is_ome:
                ome_xml = self.metadata.to_xml(
                    c=c, t=self._current_time, file_name=self.file_name, uid=self.uid
                ).encode()
        else:
            ome_xml = None

        if len(kw) > 0:
            self._views.append(kw)

        if self.is_ome:
            self.image[c].write(data, description=ome_xml, contiguous=True)
        else:
            dx, dy, dz = self.metadata.voxel_size
            md = {"spacing": dz, "unit": "um", "axes": "ZYX"}
            self.image[c].write(
                data,
                resolution=(1e4 / dx, 1e4 / dy, "CENTIMETER"),
                metadata=md,
                contiguous=True,
            )

        self._current_frame += 1

        # Check if this was the last frame to write
        # print("Switch")
        c, z, _, _ = self._cztp_indices(self._current_frame, self.metadata.per_stack)
        if (z == 0) and (c == 0):
            self.close(True)

    def generate_image_name(self, current_channel, current_time_point):
        """
        #  Generates a string for the filename
        #  e.g., CH00_000000.tif
        """
        ext = ".ome" if self.is_ome else ""
        ext += ".tiff" if self.__double_f else ".tif"
        image_name = (
            "CH0" + str(current_channel) + "_" + str(current_time_point).zfill(6) + ext
        )
        return image_name

    def _setup_write_image(self) -> None:
        """Setup N channel images for writing."""

        # Grab expected data shape from metadata
        (
            self.shape_x,
            self.shape_y,
            self.shape_c,
            self.shape_z,
            self.shape_t,
        ) = self.metadata.shape
        self.dx, self.dy, self.dz = self.metadata.voxel_size
        self.dc, self.dt = self.metadata.dc, self.metadata.dt

        # Initialize one TIFF per channel per time point
        self.image = []
        self.file_name = []
        self.uid = []
        self._views = []

        if self.metadata._multiposition:
            position_directory = os.path.join(
                self.save_directory, f"Position{self._current_position}"
            )
        else:
            position_directory = self.save_directory
        if not os.path.exists(position_directory):
            os.mkdir(position_directory)
        for ch in range(self.shape_c):
            file_name = os.path.join(
                position_directory, self.generate_image_name(ch, self._current_time)
            )
            self.image.append(
                tifffile.TiffWriter(
                    file_name, bigtiff=self.is_bigtiff, ome=False, byteorder="<"
                )
            )
            self.file_name.append(file_name)
            self.uid.append(str(uuid.uuid4()))

    def _mode_checks(self) -> None:
        self._write_mode = self._mode == "w"
        self.close()  # if anything was already open, close it
        if self._write_mode:
            self._current_frame = 0
            self._views = []
            # self._setup_write_image()
        else:
            self.read()
        self._closed = False

    def close(self, internal=False) -> None:
        if self._closed and not internal:
            return
        if self.image is None:
            return
        # internal flag needed to avoid _check_shape call until last file is written
        if self._write_mode:
            if not internal:
                self._check_shape(self._current_frame - 1, self.metadata.per_stack)
            for ch in range(len(self.image)):
                self.image[ch].close()
                if self.is_ome and len(self._views) > 0:
                    # Attach OME metadata at the end of the write
                    tifffile.tiffcomment(
                        self.file_name[ch],
                        self.metadata.to_xml(
                            c=ch,
                            t=self._current_time,
                            file_name=self.file_name,
                            uid=self.uid,
                            views=self._views,
                        ).encode(),
                    )
        else:
            self.image.close()
        if not internal:
            self._closed = True
