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
#

#  Standard Imports
import os
import logging
import shutil
import time
from datetime import datetime

# Third Party Imports
import numpy as np
from tifffile import imsave

# Local imports
from navigate.model import data_sources

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ImageWriter:
    """Class for saving acquired data to disk."""

    def __init__(
        self,
        model,
        microscope_name=None,
        data_buffer=None,
        sub_dir="",
        image_name=None,
        saving_flags=None,
        saving_config={},
    ):
        """Class for saving acquired data to disk.

        Parameters
        ----------
        model : navigate.model.model.Model
            Navigate Model class for controlling hardware/acquisition.
        data_buffer: [SharedNDArray]
            data_buffer will use model's default data_buffer if it's not specified
        sub_dir : str
            Sub-directory of self.model.configuration['experiment']
            ['Saving']['save_directory']
            indicating where to save data
        image_name : str
            Name of the image to be saved. If None, a name will be generated
        """
        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: navigate.model.model.Model: Navigate Model class for controlling
        # hardware/acquisition.
        self.model = model

        #: [SharedNDArray]: Data buffer for saving data.
        self.data_buffer = (
            self.model.data_buffer if data_buffer is None else data_buffer
        )

        #: int : Number of frames in the experiment.
        self.number_of_frames = self.model.number_of_frames

        #: array : Array of saving flags
        self.saving_flags = saving_flags

        #: str : Directory for saving data to disk.
        self.save_directory = ""

        #: str : Sub-directory for saving data to disk.
        self.sub_dir = sub_dir

        #: int : Current time point for saving data.
        self.current_time_point = 0

        #: dict : Dictionary of functions to call for each configuration.
        self.config_table = {
            "signal": {},
            "data": {"main": self.save_image, "cleanup": self.close},
        }

        #: bool: Is 32 vs 64-bit file format.
        self.big_tiff = False

        #: dict: Saving config
        self.saving_config = saving_config

        #: DataSource: Data source
        self.data_source = None

        # camera flip flags
        if self.microscope_name is None:
            self.microscope_name = self.model.active_microscope_name
        camera_config = self.model.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["camera"]
        self.flip_flags = {
            "x": camera_config.get("flip_x", False),
            "y": camera_config.get("flip_y", False),
        }

        # initialize saving
        self.initialize_saving(sub_dir, image_name)

    def save_image(self, frame_ids):
        """Save the data to disk.

        Parameters
        ----------
        frame_ids : int
            Index into self.model.data_buffer.
        """

        for idx in frame_ids:

            if (idx < 0) or (idx > (self.number_of_frames - 1)):
                msg = f"Received invalid index {idx}. Skipping this frame."
                logger.debug(f"Received invalid index: {msg}.")
                continue

            # check the saving flag
            if self.saving_flags:
                if not self.saving_flags[idx]:
                    continue
                self.saving_flags[idx] = False

            # Identify channel, z, time, and position indices
            c_idx, z_idx, t_idx, p_idx = self.data_source._cztp_indices(
                self.data_source._current_frame, self.data_source.metadata.per_stack
            )

            if c_idx == 0 and z_idx == 0:
                # Initialize MIP array with same number of channels as the data
                self.mip = np.ndarray(
                    (
                        int(self.data_source.shape_c),
                        int(self.data_source.shape_y),
                        int(self.data_source.shape_x),
                    )
                ).astype(np.uint16)

            # flip image if necessary
            if self.flip_flags["x"] and self.flip_flags["y"]:
                image = self.data_buffer[idx][::-1, ::-1]
            elif self.flip_flags["x"]:
                image = self.data_buffer[idx][:, ::-1]
            elif self.flip_flags["y"]:
                image = self.data_buffer[idx][::-1, :]
            else:
                image = self.data_buffer[idx]
            # Save data to disk
            try:
                start_time = time.time()
                self.data_source.write(
                    image,
                    x=self.model.data_buffer_positions[idx][0],
                    y=self.model.data_buffer_positions[idx][1],
                    z=self.model.data_buffer_positions[idx][2],
                    theta=self.model.data_buffer_positions[idx][3],
                    f=self.model.data_buffer_positions[idx][4],
                )
                logger.info(f"C: {c_idx}, Z:{z_idx}, T:{t_idx}, P:{p_idx}, Write Time:"
                            f" {time.time() - start_time}")

                # Update MIP
                self.mip[c_idx, :, :] = np.maximum(self.mip[c_idx, :, :], image)

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
                            self.mip[c_save_idx, :, :],
                        )
            except Exception as e:
                from traceback import format_exc

                # Close the image, stop the acquisition, log error, and notify user.
                self.close()
                self.model.stop_acquisition = True
                self.model.event_queue.put(
                    ("warning", f"Error - ImageWriter: {format_exc()}")
                )
                logger.debug(f"Error - ImageWriter: {e}")
                return

    def generate_image_name(self, current_channel, ext=".tif"):
        """Generates a string for the filename, e.g., CH00_000000.tif.

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

    def close(self):
        """Close the data source we are writing to.
        """
        self.data_source.close()

    def calculate_and_check_disk_space(self):
        """Estimate the size of the data that will be written to disk, and confirm
        that sufficient disk space is available. Also evaluates whether
        big-tiff or tiff is needed. Tiff file formats were designed for 32-bit
        operating systems, whereas big-tiff was designed for 64-bit operating systems.

        Assumes 16-bit image type, without compression."""

        # Return disk usage statistics in bytes
        _, _, free = shutil.disk_usage(self.save_directory)
        logger.info(f"Free Disk Space: {free}")

        # Calculate the size in bytes.
        image_size = self.data_source.nbytes
        logger.info(f"Anticipated Image Size: {image_size}")

        # Confirm that there is enough disk space to save the data.
        if free < image_size:
            logger.debug("Image Writer: Insufficient Disk Space Estimated.")
            self.model.stop_acquisition = True
            self.model.event_queue.put(
                ("warning", "Insufficient Disk Space. Acquisition Terminated")
            )
            return

        # TIFF vs Big-TIFF Comparison
        if (self.file_type == "TIFF") or (self.file_type == "OME-TIFF"):
            if image_size > 2**32:
                self.data_source.set_bigtiff(True)
                logger.info("Big-TIFF Format Selected.")
            else:
                self.data_source.set_bigtiff(False)

    def get_saving_file_name(self, sub_dir="", image_name=None):
        self.sub_dir = sub_dir
        # create the save directory if it doesn't already exist
        self.save_directory = os.path.join(
            self.model.configuration["experiment"]["Saving"]["save_directory"],
            self.sub_dir,
        )
        logger.info(f"Save Directory: {self.save_directory}")
        try:
            if not os.path.exists(self.save_directory):
                try:
                    os.makedirs(self.save_directory)
                    logger.debug(f"Save Directory Created - {self.save_directory}")
                except OSError:
                    logger.debug(
                        f"Unable to Create Save Directory - {self.save_directory}"
                    )
                    self.model.stop_acquisition = True
                    self.model.event_queue.put(
                        "warning",
                        "Unable to Create Save Directory. Acquisition Terminated",
                    )
                    return
        except FileNotFoundError as e:
            logger.error(f"Unable to Create Save Directory - {self.save_directory}")

        # Set up the file name and path in the save directory
        #: str : File type for saving data.
        self.file_type = self.model.configuration["experiment"]["Saving"]["file_type"]
        logger.info(f"Saving Data as File Type: {self.file_type}")

        current_channel = self.model.active_microscope.current_channel
        ext = "." + self.file_type.lower().replace(" ", ".").replace("-", ".")
        if image_name is None:
            image_name = self.generate_image_name(current_channel, ext=ext)
        file_name = os.path.join(self.save_directory, image_name)

        if os.path.exists(file_name):
            current_time = datetime.now().strftime("%H-%M")
            return self.create_saving_directory(f"{sub_dir}-{current_time}")

        return file_name

    def initialize_saving(self, sub_dir="", image_name=None):

        if self.data_source is not None:
            self.data_source.close()
            self.data_source = None

        self.current_time_point = 0

        file_name = self.get_saving_file_name(sub_dir, image_name)
        print("saving to new file:", file_name)

        # create the MIP directory if it doesn't already exist
        #: np.ndarray : Maximum intensity projection image.
        self.mip = None

        #: str : Directory for saving maximum intensity projection images.
        self.mip_directory = os.path.join(self.save_directory, "MIP")
        try:
            if not os.path.exists(self.mip_directory):
                try:
                    os.makedirs(self.mip_directory)
                    logger.debug(f"MIP Directory Created - {self.mip_directory}")
                except OSError:
                    logger.debug(
                        f"Unable to Create MIP Directory - {self.mip_directory}"
                    )
                    self.model.stop_acquisition = True
                    self.model.event_queue.put(
                        "warning",
                        "Unable to create MIP Directory. Acquisition Terminated.",
                    )
                    return
        except FileNotFoundError as e:
            logger.error("Image Writer: Unable to create MIP directory.")

        

        # Initialize data source, pointing to the new file name
        #: navigate.model.data_sources.DataSource : Data source for saving data to disk.
        self.data_source = data_sources.get_data_source(self.file_type)(
            file_name=file_name
        )

        # Pass experiment and configuration to metadata
        self.data_source.set_metadata_from_configuration_experiment(
            self.model.configuration, self.microscope_name
        )

        self.data_source.set_metadata(self.saving_config)

        # Make sure that there is enough disk space to save the data.
        self.calculate_and_check_disk_space()
