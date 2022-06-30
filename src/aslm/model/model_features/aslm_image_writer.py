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

# Third Party Imports
from tifffile import imsave
import zarr


# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class ImageWriter:
    def __init__(self, model, sub_dir=''):
        self.model = model
        self.save_directory = os.path.join(self.model.experiment.Saving['save_directory'], sub_dir)
        self.num_of_channels = len(self.model.experiment.MicroscopeState['channels'].keys())
        self.data_buffer = self.model.data_buffer
        self.current_time_point = 0
        self.file_type = self.model.experiment.Saving['file_type']

        self.config_table = {'signal':{},
                            'data': {'main': self.write_tiff}}

        # creat saving folder if not exits
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

    def __del__(self):
        pass

    def save_image(self, frame_ids):
        '''
        Wrapper to give Image Writer some saving decision making, this function will be called from model.
        '''
        self.save_directory = self.model.experiment.Saving['save_directory']
        self.file_type = self.model.experiment.Saving['file_type']


        if self.file_type == "Zarr":
            self.write_zarr(frame_ids)
        elif self.file_type == "TIFF":
            self.write_tiff(frame_ids)


    def write_zarr(self, frame_ids):
        '''
        Will take in camera frames and move data fom SharedND Array into a Zarr Array.
        If there is more than one channel there will be that many frames ie if there are 3 channels selected there should be three frames.
        Making the assumption there is only one frame per channel on a single acquisition
        '''

        # Getting needed info, I am doing it in the function because i think if we do not reinit the class,
        # save directory will be a stagnant var. If we just leave
        # self.model = model then that ref will alwasy be up to date
        num_of_channels = len(self.model.experiment.MicroscopeState['channels'].keys())
        data_buffer = self.model.data_buffer

        # Getting allocation parameters for zarr array
        xsize = self.model.experiment.CameraParameters['x_pixels']
        ysize = self.model.experiment.CameraParameters['y_pixels']

        # Boolean flag to decide which order for saving, by stack or slice.
        # Code is brute force to make it clear, can be sanitized if need be
        by_stack = False
        by_slice = False
        if self.model.experiment.MicroscopeState['stack_cycling_mode'] == 'per_stack':
            by_stack = True
        if self.model.experiment.MicroscopeState['stack_cycling_mode'] == 'per_z':
            by_slice = True

        # Getting amount of slices
        zslice = int(self.model.experiment.MicroscopeState['number_z_steps'])

        '''
        Allocate zarr array with values needed
        X Pixel Size, Y Pixel Size, Z Slice, Channel Num, Frame ID
        Chunks set to size of each image with the corresponding additional data
        Numpy data type = dtype='uint16'
        z[:,:,0,0,0] = 2D array at zslice=0, channel=0, frame=0
        '''

        z = zarr.zeros((xsize, ysize, zslice, self.num_of_channels, len(frame_ids)), 
                        chunks = (xsize, ysize, 1, 1, 1), dtype='uint16')

        # Get the currently selected channels, the order is implicit
        channels = self.model.experiment.MicroscopeState['channels']
        selected_channels = []
        prefix_len = len('channel_') # helps get the channel index
        for channel_key in channels:
            channel_idx = int(channel_key[prefix_len:])
            channel = channels[channel_key]

            # Put selected channels index into list
            if channel['is_selected'] is True:
                selected_channels.append(channel_idx)
        
        # Copy data to Zarr
        # Saving Acq By Slice
        '''
        Starts on first channel and increments with the loop. Each image is saved by slice, channel and timepoint.
        After each channel has been taken off data buffer then the slice is incremented.
        After the amount of slices set by zslice has been reached, time is then incremented.
        TODO do we need to store the actual channel number? Or just make sure that frames are in an order than channels can be interpreted?
        '''
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
        '''
        Starts on first channel and increments thru loop. 
        Each increment of the loop increases the slice index.
        Once the slice has reached max count increment to next channel.
        After all channels and slices have been incremented, increase the time by one.
        '''
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
                
        save_path = os.path.join(self.save_directory, "file.zarr")
        zarr.save(save_path, z)

    def write_raw(self, image):
        pass

    def write_n5(self, image):
        pass

    def write_h5(self, image):
        pass

    def write_tiff(self, frame_ids):
        r"""Write data to disk as a tiff

        Parameters
        __________
        frame_ids :
        """
        print("frame_ids type:", type(frame_ids))
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

    def generate_meta_data(self):
        print('meta data: write', self.model.frame_id)