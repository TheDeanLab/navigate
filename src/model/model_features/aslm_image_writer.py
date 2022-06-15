"""
ASLM camera communication classes.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

#  Standard Imports
import os
import logging
from pathlib import Path

# Third Party Imports
from tifffile import imsave
import zarr


# Local Imports

# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

class ImageWriter:
    def __init__(self, model):
        self.model = model
        self.save_directory = self.model.experiment.Saving['save_directory']
        self.num_of_channels = len(self.model.experiment.MicroscopeState['channels'].keys())
        self.data_buffer = self.model.data_buffer
        self.current_time_point = 0

    def __del__(self):
        pass

    def copy_to_zarr(self, frame_ids):
        '''
        Will take in camera frames and move data fom SharedND Array into a Zarr Array.
        If there is more than one channel there will be that many frames ie if there are 3 channels selected there should be three frames.
        Making the assumption there is only one frame per channel on a single acquisition
        '''

        # Getting 

        # Getting allocation parameters for zarr array
        xsize = self.model.experiment.CameraParameters['x_pixels']
        ysize = self.model.experiment.CameraParameters['y_pixels']
        image_mode = self.model.experiment.MicroscopeState['image_mode']
        if image_mode == 'single':
            zslice = 1
        else:
            zslice = self.model.experiment.MicroscopeState['number_z_steps']


        # Allocate zarr array with values needed
        # X Pixel Size, Y Pixel Size, Z Slice, Channel Num, Frame ID
        # Chunks set to False as we are not currently accessing the array like the SharedNDArray just using it to write to disk and then convert
        # Numpy data type = dtype='uint16'
        z = zarr.zeros((xsize, ysize, zslice, self.num_of_channels, len(frame_ids)), chunks=False , dtype='uint16')

        # z[:,:,0,0,0] = 2D array at zslice=0, channel=0, frame=0

        # Get the currently selected channels, the order is implicit
        channels = self.experiment.MicroscopeState['channels']
        selected_channels = []
        prefix_len = len('channel_') # helps get the channel index
        for channel_key in channels:
            channel_idx = int(channel_key[prefix_len:])
            channel = channels[channel_key]

            # Put selected channels index into list
            if channel['is_selected'] is True:
                selected_channels.append(channel_idx)
        
        # Copy data to Zarr
        for frame in frame_ids:







    def write_raw(self, image):
        pass

    def write_n5(self, image):
        pass

    def write_h5(self, image):
        pass

    def write_tiff(self, frame_ids):
        current_channel = self.model.current_channel
        for idx in frame_ids:
            image_name = self.generate_image_name(current_channel)
            imsave(os.path.join(self.save_directory, image_name), self.model.data_buffer[idx])

    def generate_image_name(self, current_channel):
        """
        #  Generates a string for the filename
        #  e.g., CH00_000000.tif
        """
        image_name = "CH0" + str(current_channel) + "_" + str(self.current_time_point).zfill(6) + ".tif"
        self.current_time_point += 1
        return image_name