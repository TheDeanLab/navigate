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

# Third Party Imports
import zarr
import numpy.typing as npt

# Local imports
from .data_source import DataSource


class ZarrDataSource(DataSource):
    def __init__(self, file_name: str = None, mode: str = "w") -> None:
        super().__init__(file_name, mode)

    def write(self, data: npt.ArrayLike, **kw) -> None:
        z = self.copy_to_zarr(data)

        zarr.save(self.file_name, z)

    def copy_to_zarr(self, frame_ids):
        """Write data to Zarr.

        Will take in camera frames and move data fom SharedND Array into a Zarr Array.
        If there is more than one channel there will be that many frames.
        For example, if there are 3 channels selected there should be three frames.
        Making the assumption there is only one frame per channel on a single
        acquisition
        """

        # Getting needed info, I am doing it in the function because i think if we do
        # not reinit the class,
        # save directory will be a stagnant var. If we just leave
        # self.model = model then that ref will alwasy be up to date
        num_of_channels = len(
            self.model.configuration["experiment"]["MicroscopeState"]["channels"].keys()
        )
        data_buffer = self.model.data_buffer

        # Getting allocation parameters for zarr array
        xsize = self.model.configuration["experiment"]["CameraParameters"]["x_pixels"]
        ysize = self.model.configuration["experiment"]["CameraParameters"]["y_pixels"]

        # Boolean flag to decide which order for saving, by stack or slice.
        # Code is brute force to make it clear, can be sanitized if need be
        by_stack = False
        by_slice = False
        if (
            self.model.configuration["experiment"]["MicroscopeState"][
                "stack_cycling_mode"
            ]
            == "per_stack"
        ):
            by_stack = True
        if (
            self.model.configuration["experiment"]["MicroscopeState"][
                "stack_cycling_mode"
            ]
            == "per_z"
        ):
            by_slice = True

        # Getting amount of slices
        zslice = int(
            self.model.configuration["experiment"]["MicroscopeState"]["number_z_steps"]
        )

        """
        Allocate zarr array with values needed
        X Pixel Size, Y Pixel Size, Z Slice, Channel Num, Frame ID
        Chunks set to size of each image with the corresponding additional data
        Numpy data type = dtype='uint16'
        z[:,:,0,0,0] = 2D array at zslice=0, channel=0, frame=0
        """

        z = zarr.zeros(
            (xsize, ysize, zslice, self.num_of_channels, len(frame_ids)),
            chunks=(xsize, ysize, 1, 1, 1),
            dtype="uint16",
        )

        # Get the currently selected channels, the order is implicit
        channels = self.model.configuration["experiment"]["MicroscopeState"]["channels"]
        selected_channels = []
        prefix_len = len("channel_")  # helps get the channel index
        for channel_key in channels:
            channel_idx = int(channel_key[prefix_len:])
            channel = channels[channel_key]

            # Put selected channels index into list
            if channel["is_selected"] is True:
                selected_channels.append(channel_idx)

        # Copy data to Zarr
        # Saving Acq By Slice
        """
        Starts on first channel and increments with the loop. Each image is saved by
        slice, channel and timepoint.
        After each channel has been taken off data buffer then the slice is incremented.
        After the amount of slices set by zslice has been reached, time is then
        incremented.
        TODO do we need to store the actual channel number? Or just make sure that
        frames are in an order than channels can be interpreted?
        """
        if by_slice:
            time = 0
            slice = 0
            chan = 0
            for idx, frame in enumerate(frame_ids):
                img = data_buffer[frame]
                chan = idx % num_of_channels
                z[:, :, slice, chan, time] = img
                if chan == num_of_channels - 1:
                    slice += 1
                if slice == zslice:
                    time += 1
                    slice = 0

        # Saved by stack
        """
        Starts on first channel and increments thru loop.
        Each increment of the loop increases the slice index.
        Once the slice has reached max count increment to next channel.
        After all channels and slices have been incremented, increase the time by one.
        """
        if by_stack:
            time = 0
            slice = 0
            chan = 0
            for idx, frame in enumerate(frame_ids):
                image = data_buffer[frame]
                slice = idx % zslice
                z[:, :, slice, chan, time] = image
                if chan == num_of_channels - 1 and slice == zslice - 1:
                    time += 1
                    chan = 0
                elif slice == zslice - 1:
                    chan += 1
        return z