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

#  Standard Imports
import os
import uuid
from pathlib import Path
import logging

# Third Party Imports
import tifffile
import numpy.typing as npt
from numpy import stack

# Local imports
from .data_source import DataSource, DataReader
from ..metadata_sources.metadata import Metadata
from ..metadata_sources.ome_tiff_metadata import OMETIFFMetadata


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class TiffDataSource(DataSource):
    """Data source for TIFF files."""

    def __init__(
        self, file_name: str = "", mode: str = "w", is_bigtiff: bool = False
    ) -> None:
        """Initialize a TIFF data source.

        Parameters
        ----------
        file_name : str
            Path to file.
        mode : str
            File mode. "r" for read, "w" for write.
        is_bigtiff : bool
            Is this a bigtiff file?
        """
        #: np.ndarray: Image data
        self.image = None
        self._views = []

        super().__init__(file_name, mode)

        #: str: Directory to save the data to.
        self.save_directory = Path(self.file_name).parent

        # Is this an OME-TIFF?
        # TODO: check the header, rather than use the file extension
        if self.file_name.endswith(".ome.tiff") or self.file_name.endswith(".ome.tif"):
            self._is_ome = True
            #: Metadata: Metadata object
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
        """Return the image data as a numpy array.

        Returns
        -------
        npt.ArrayLike
            Image data.
        """
        self.mode = "r"
        return self.image.asarray()

    @property
    def is_bigtiff(self) -> bool:
        """Is this a bigtiff file?

        Returns
        -------
        bool
            Is this a bigtiff file?
        """
        if self._write_mode:
            return self._is_bigtiff
        else:
            return self.image.is_bigtiff

    def set_bigtiff(self, is_bigtiff: bool) -> None:
        """Set whether this is a bigtiff file.

        Parameters
        ----------
        is_bigtiff : bool
            Is this a bigtiff file?
        """
        self._is_bigtiff = is_bigtiff

    @property
    def is_ome(self) -> bool:
        """Is this an OME-TIFF file?

        Returns
        -------
        bool
            Is this an OME-TIFF file?
        """
        if self._write_mode:
            return self._is_ome
        else:
            return self.image.is_ome

    def read(self) -> None:
        """Read a tiff file."""
        self.mode = "r"
        self.image = tifffile.TiffFile(self.file_name)

        # TODO: Parse metadata
        for i, ax in enumerate(list(self.image.series[0].axes)):
            if ax == "Q":
                # TODO: This is a hack for tifffile. Find a way to remove this.
                ax = "Z"
            setattr(self, f"shape_{ax.lower()}", self.data.shape[i])

    def get_data(self, timepoint: int=0, position: int=0, channel: int=0, z: int=-1, resolution: int=1) -> npt.ArrayLike:
        """Get data according to timepoint, position, channel and z-axis id

        Parameters
        ----------
        timepoint : int
            The timepoint value
        position : int
            The position id in multi-position table
        channel : int
            The channel id
        z : int
            The index of Z in a Z-stack. 
            Return all z if -1.
        resolution : int
            values from 1, 2, 4, 8
            Not supported for now.

        Returns
        -------
        data : npt.ArrayLike
            Image data
        """
        # TODO: may need to support .tif
        file_suffix = ".ome.tiff" if self.is_ome else ".tiff"
        filename = os.path.join(self.save_directory, f"Position{position}", f"CH{channel:02d}_{timepoint:06d}{file_suffix}")

        if not os.path.exists(filename):
            return None

        image = tifffile.TiffFile(filename)
        if z < 0:
            return TiffReader(image)
        
        z_num = len(image.pages)
        if z < z_num:
            return image.pages[z].asarray()
        
        return None

    def write(self, data: npt.ArrayLike, **kw) -> None:
        """Writes 2D image to the data source.

        One channel, all z-position, one timepoint = one stack.
        N channels are opened simultaneously for writing.
        At each time point, a new file is opened for each channel.

        Parameters
        ----------
        data : npt.ArrayLike
            Data to write to file.
        kw : dict
            Keyword arguments to pass to tifffile.imsave.
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
            md = {"spacing": dz, "unit": "um", "axes": "ZYX", "channel": c, "timepoint": self._current_time}
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
        """Generates a string for the filename, e.g., CH00_000000.tif

        Parameters
        ----------
        current_channel : int
            Current channel index.
        current_time_point : int
            Current time point index.

        Returns
        -------
        str
            Image name.
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

    def close(self, internal=False) -> None:
        """Close the file.

        Parameters
        ----------
        internal : bool
            Internal flag. Do not close if True.
        """
        if self._closed and not internal:
            return
        if self.image is None:
            return
        # internal flag needed to avoid _check_shape call until last file is written
        if self.mode == "w":
            if not internal:
                self._check_shape(self._current_frame - 1, self.metadata.per_stack)
        if type(self.image) == list:
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


class TiffReader(DataReader):
    def __init__(self, tiff_file: tifffile.TiffFile):
        self.tiff = tiff_file

    @property
    def shape(self):
        page_number = len(self.tiff.pages)

        x, y = self.tiff.pages[0].shape

        return (page_number, x, y)
    
    def __getitem__(self, index):

        if isinstance(index, int):
            # Return the entire page as a NumPy array
            return self.tiff.pages[index].asarray()
        
        elif isinstance(index, slice):
            # Handle case for slicing all pages
            pages = [self.tiff.pages[i].asarray() for i in range(index.start, index.stop)]
            return stack(pages, axis=0)
        
        elif isinstance(index, tuple):
            # Check if the first index is an integer (page index)
            if isinstance(index[0], int):
                page_index = index[0]
                if len(index) == 2:
                    return self.tiff.pages[page_index].asarray()[index[1]]
                elif len(index) == 3:
                    return self.tiff.pages[page_index].asarray()[index[1], index[2]]
            elif isinstance(index[0], slice):
                if len(index) == 2:
                    pages = [self.tiff.pages[i].asarray()[index[1]] for i in range(index.start, index.stop)]
                    
                elif len(index) == 3:
                    pages = [self.tiff.pages[i].asarray()[index[1], index[2]] for i in range(index.start, index.stop)]
                return stack(pages, axis=0)
        
        logger.debug(f"TiffReader: Invalid indexing format. {index}")
        return None
    
    def __array__(self):
        return self.tiff.asarray()
