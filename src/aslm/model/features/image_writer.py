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
#

#  Standard Imports
import os
import logging

# Third Party Imports
import numpy as np
from tifffile import imsave

# Local imports
from aslm.model import data_sources

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ImageWriter:
    def __init__(self, model, sub_dir="", image_name=None):
        """Class for saving acquired data to disk.

        Parameters
        ----------
        model : aslm.model.model.Model
            ASLM Model class for controlling hardware/acquisition.
        sub_dir : str
            Sub-directory of self.model.configuration['experiment']
            ['Saving']['save_directory']
            indicating where to save data
        image_writer : str
            Optionally override the generate_image_name() naming scheme.

        Returns
        -------
        None

        Attributes
        ----------
        model : aslm.model.model.Model
            ASLM Model class for controlling hardware/acquisition.
        data_source : aslm.model.data_sources.DataSource
            Data source for saving data to disk.
        mip_directory : str
            Directory for saving maximum intensity projection images.
        mip : np.ndarray
            Maximum intensity projection image.
        current_time_point : int
            Current time point for saving data.

        Examples
        --------
        >>> model = aslm.model.model.Model()
        >>> image_writer = aslm.model.image_writer.ImageWriter(model)
        """
        self.model = model
        self.save_directory = ""
        self.sub_dir = sub_dir
        self.num_of_channels = len(
            [
                k
                for k, v in self.model.configuration["experiment"]["MicroscopeState"][
                    "channels"
                ].items()
                if v["is_selected"]
            ]
        )
        self.data_buffer = self.model.data_buffer
        self.current_time_point = 0
        self.config_table = {
            "signal": {},
            "data": {"main": self.save_image, "cleanup": self.close},
        }

        # create the save directory if it doesn't already exist
        self.save_directory = os.path.join(
            self.model.configuration["experiment"]["Saving"]["save_directory"],
            self.sub_dir,
        )

        try:
            # create saving folder if it does not exist
            if not os.path.exists(self.save_directory):
                os.makedirs(self.save_directory)
        except FileNotFoundError as e:
            logger.debug(
                f"ASLM Image Writer - Cannot create directory {self.save_directory}. "
                f"Maybe the drive does not exist?"
            )
            logger.exception(e)

        # create the maximum intensity projection directory if it doesn't already exist
        self.mip = None
        self.mip_directory = os.path.join(self.save_directory, "MIP")
        try:
            # create saving folder if not exits
            if not os.path.exists(self.mip_directory):
                os.makedirs(self.mip_directory)
        except FileNotFoundError as e:
            logger.debug(
                f"ASLM Image Writer - "
                f"Cannot create MIP directory {self.mip_directory}. "
                f"Maybe the drive does not exist?"
            )
            logger.exception(e)

        # Set up the file name and path in the save directory
        self.file_type = self.model.configuration["experiment"]["Saving"]["file_type"]
        current_channel = self.model.active_microscope.current_channel
        ext = "." + self.file_type.lower().replace(" ", ".").replace("-", ".")
        if image_name is None:
            image_name = self.generate_image_name(current_channel, ext=ext)
        file_name = os.path.join(self.save_directory, image_name)

        # Initialize data source, pointing to the new file name
        self.data_source = data_sources.get_data_source(self.file_type)(file_name)

        # Pass experiment and configuration to metadata
        self.data_source.set_metadata_from_configuration_experiment(
            self.model.configuration
        )

    def save_image(self, frame_ids):
        """Save the data to disk.

        Parameters
        ----------
        frame_ids : int
            Index into self.model.data_buffer.

        Returns
        -------
        None

        Examples
        --------
        >>> self.save_image(0)
        """

        for idx in frame_ids:
            # Identify channel, z, time, and position indices
            c_idx, z_idx, t_idx, p_idx = self.data_source._cztp_indices(idx)

            if c_idx == 0 and z_idx == 0 or idx == 0:
                # Initialize MIP array with same number of channels as the data
                self.mip = np.ndarray(
                    (
                        int(self.data_source.shape_c),
                        int(self.data_source.shape_y),
                        int(self.data_source.shape_x),
                    )
                ).astype(np.uint16)

            # Save data to disk
            self.data_source.write(
                self.model.data_buffer[idx],
                x=self.model.data_buffer_positions[idx][0],
                y=self.model.data_buffer_positions[idx][1],
                z=self.model.data_buffer_positions[idx][2],
                theta=self.model.data_buffer_positions[idx][3],
                f=self.model.data_buffer_positions[idx][4],
            )

            # Update MIP
            self.mip[c_idx, :, :] = np.maximum(
                self.mip[c_idx, :, :], self.model.data_buffer[idx]
            )

            # Save the MIP
            if (c_idx == self.data_source.shape_c - 1) and (
                z_idx == self.data_source.shape_z - 1
            ):
                for c_save_idx in range(self.data_source.shape_c):
                    mip_name = (
                        "P"
                        + str(p_idx).zfill(4)
                        + "_"
                        + "CH0"
                        + str(c_save_idx)
                        + "_"
                        + str(t_idx).zfill(6)
                        + ".tif"
                    )
                    imsave(
                        os.path.join(self.mip_directory, mip_name),
                        self.mip[c_idx, :, :],
                    )

    def generate_image_name(self, current_channel, ext=".tif"):
        """
        Generates a string for the filename, e.g., CH00_000000.tif.

        Parameters
        ----------
        current_channel : int
            Index into self.model.configuration['experiment']
            ['MicroscopeState']['channels']
            of saved color channel.

        ext : str
            File extension, e.g., '.tif'

        Returns
        -------
        str
            File name, e.g., CH00_000000.tif

        Examples
        --------
        >>> model = aslm.model.model.Model()
        >>> image_writer = aslm.model.image_writer.ImageWriter(model)
        >>> image_writer.generate_image_name(current_channel=0)
        'CH00_000000.tif'

        """
        image_name = (
            "CH0"
            + str(current_channel)
            + "_"
            + str(self.current_time_point).zfill(6)
            + ext
        )
        self.current_time_point += 1
        return image_name

    def generate_meta_data(self):
        """Generate meta data for the image.

        TODO: Is this a vestigial function? DELETE???

        Returns
        -------
        dict
            Meta data for the image.

        Examples
        --------
        >>> model = aslm.model.model.Model()
        >>> image_writer = aslm.model.image_writer.ImageWriter(model)
        >>> image_writer.generate_meta_data()
        """
        print("meta data: write", self.model.frame_id)
        return True

    def close(self):
        """Close the data source we are writing to.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> self.close()
        """
        self.data_source.close()
