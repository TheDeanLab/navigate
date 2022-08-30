"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
# import numpy as np

# Local imports
from aslm.model.model_features import data_sources
# from aslm.tools.image import text_array

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ImageWriter:
    r"""Class for saving acquired data to disk.

    """
    def __init__(self, model, sub_dir=''):
        self.model = model
        self.save_directory = ''
        self.sub_dir = sub_dir
        # self.num_of_channels = len(self.model.experiment.MicroscopeState['channels'].keys())
        self.num_of_channels = len([k for k, v in self.model.experiment.MicroscopeState['channels'].items() if v['is_selected']])
        self.data_buffer = self.model.data_buffer
        self.current_time_point = 0
        self.config_table = {'signal': {},
                             'data': {'main': self.save_image,
                                      'cleanup': self.close}}

        # create the save directory if it doesn't already exist
        self.save_directory = os.path.join(self.model.experiment.Saving['save_directory'], self.sub_dir)
        try:
            # create saving folder if not exits
            if not os.path.exists(self.save_directory):
                os.makedirs(self.save_directory)
        except FileNotFoundError as e:
            logger.debug(f"ASLM Image Writer - Cannot create directory {self.save_directory}. Maybe the drive does not exist?")
            logger.exception(e)
        
        # Set up the file name and path in the save directory
        self.file_type = self.model.experiment.Saving['file_type']
        current_channel = self.model.current_channel
        ext = '.' + self.file_type.lower().replace(' ','.').replace('-','.')
        image_name = self.generate_image_name(current_channel, ext=ext)
        file_name = os.path.join(self.save_directory, image_name)

        # Initialize data source, pointing to the new file name
        self.data_source = data_sources.get_data_source(self.file_type)(file_name)

        # Pass experiment and configuration to metadata
        self.data_source.set_metadata_from_configuration_experiment(self.model.configuration, 
                                                                    self.model.experiment)

    def save_image(self, frame_ids):
        r"""Save the data to disk.

        Parameters
        ----------
        frame_ids : int
            Frame ID.
        """
        for idx in frame_ids:
            # data = self.model.data_buffer[idx]
            # text_im = text_array(f"Image {idx}")
            # data[:text_im.shape[0], :text_im.shape[1]] += text_im.astype('uint16')*np.maximum(np.max(data)//2, 1)
            self.data_source.write(self.model.data_buffer[idx],  # data,
                                   x=self.model.data_buffer_positions[idx][0],
                                   y=self.model.data_buffer_positions[idx][1],
                                   z=self.model.data_buffer_positions[idx][2],
                                   theta=self.model.data_buffer_positions[idx][3],
                                   f=self.model.data_buffer_positions[idx][4])

    def generate_image_name(self, current_channel, ext=".tif"):
        """
        #  Generates a string for the filename
        #  e.g., CH00_000000.tif
        """
        image_name = "CH0" + str(current_channel) + "_" + str(self.current_time_point).zfill(6) + ext
        self.current_time_point += 1
        return image_name

    def generate_meta_data(self):
        print('meta data: write', self.model.frame_id)
        return True
    
    def close(self):
        self.data_source.close()
