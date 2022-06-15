"""
ASLM sub-controller for the camera image display.

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
# Standard Library Imports
import tkinter as tk
import logging

# Third Party Imports
import cv2
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np

# Local Imports
from controller.sub_controllers.gui_controller import GUI_Controller

# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)


class Camera_View_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # Getting Widgets/Buttons
        self.image_metrics = view.image_metrics.get_widgets()
        self.image_palette = view.scale_palette.get_widgets()
        self.canvas = self.view.canvas

        # Binding for adjusting the lookup table min and max counts.
        # keys = ['Autoscale', 'Min','Max']
        self.image_palette['Autoscale'].widget.config(command=self.toggle_min_max_buttons)
        self.image_palette['Min'].widget.config(command=self.update_min_max_counts)
        self.image_palette['Max'].widget.config(command=self.update_min_max_counts)

        # Bindings for changes to the LUT
        # keys = ['Gray','Gradient','Rainbow']
        self.image_palette['Gray'].widget.config(command=self.update_LUT)
        self.image_palette['Gradient'].widget.config(command=self.update_LUT)
        self.image_palette['Rainbow'].widget.config(command=self.update_LUT)

        # Bindings for key events
        global count
        count = 0
        self.canvas.bind("<Button-1>", self.left_click)
        #Mouse Hovering
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)


        #  Stored Images
        self.tk_image = None
        self.image = None
        self.saturated_pixels = None

        # Widget Defaults
        self.autoscale = True
        self.max_counts = None
        self.min_counts = None
        self.apply_cross_hair = True
        self.mode = 'stop'

        # Colormap Information
        self.colormap = 'gray'
        self.gray_lut = plt.get_cmap('gist_gray')
        self.gradient_lut = plt.get_cmap('plasma')
        self.rainbow_lut = plt.get_cmap('afmhot')

        self.image_count = 0
        self.temp_array = None
        self.rolling_frames = 1
        self.live_subsampling = self.parent_controller.configuration.CameraParameters['display_live_subsampling']
        self.bit_depth = 8  # bit-depth for PIL presentation.

    def on_enter(self, event):
        print("Mouse has entered")
        self.canvas.bind("<MouseWheel>", self.mouse_track)
    def on_leave(self, event):
        print("Mouse has left")


    def mouse_track(self, event):
        global count
        if event.delta == -1:
            count -= 1
        if event.delta == 1:
            count += 1
        print(count)
    
    
    def get_count () :
        global count
        return count
    
    def initialize(self, name, data):
        '''
        # Function that sets widgets based on data given from main controller/config
        '''
        # Pallete section (colors, autoscale, min/max counts)
        # keys = ['Frames to Avg', 'Image Max Counts', 'Channel']
        if name == 'minmax':
            min = data[0]
            max = data[1]

            # Invoking defaults
            self.image_palette['Gray'].widget.invoke()
            self.image_palette['Autoscale'].widget.invoke()

            # Populating defaults
            self.image_palette['Min'].set(min)
            self.image_palette['Max'].set(max)
            self.image_palette['Min'].widget['state'] = 'disabled'
            self.image_palette['Max'].widget['state'] = 'disabled'

        # Image Metrics section
        if name == 'image':
            frames = data[0]
            # Populating defaults
            self.image_metrics['Frames'].set(frames)

    #  Set mode for the execute statement in main controller

    def set_mode(self, mode=''):
        self.mode = mode

    def populate_view(self):
        # self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1.5)
        pass

    def left_click(self, event):
        if self.image is not None:
            # If True, make False. If False, make True.
            self.apply_cross_hair = not self.apply_cross_hair
            self.add_crosshair()
            self.apply_LUT()
            self.populate_image()

    def update_max_counts(self):
        """
        #  Function gets the number of frames to average from the VIEW.
        #  If frames to average == 0 or 1, provides the maximum value from the last acquired data.
        #  If frames to average >1, initializes a temporary array, and appends each subsequent image to it.
        #  Once the number of frames to average has been reached, deletes the first image in.
        #  Reports the rolling average.
        """
        self.rolling_frames = int(self.image_metrics['Frames'].get())
        if self.rolling_frames == 0:
            # Cannot average 0 frames. Set to 1, and report max intensity
            self.image_metrics['Frames'].set(1)
            self.image_metrics['Image'].set(self.max_counts)

        elif self.rolling_frames == 1:
            self.image_metrics['Image'].set(self.max_counts)

        else:
            #  Rolling Average
            self.image_count = self.image_count + 1
            if self.image_count == 1:
                # First frame of the rolling average
                self.temp_array = self.image
                self.image_metrics['Image'].set(self.max_counts)
            else:
                # Subsequent frames of the rolling average
                self.temp_array = np.dstack((self.temp_array, self.image))
                if np.shape(self.temp_array)[2] > self.rolling_frames:
                    self.temp_array = np.delete(self.temp_array, 0, 2)

                # Update GUI
                self.image_metrics['Image'].set(np.max(self.temp_array))

                if self.verbose:
                    print("Rolling Average: ", self.image_count, self.rolling_frames)
                logger.debug(f"Rolling Average: , {self.image_count}, {self.rolling_frames}")

    def downsample_image(self):
        """
        #  Down-sample the data for image display according to the configuration file.
        """
        if self.live_subsampling != 1:
            self.image = cv2.resize(self.image,
                                    (int(np.shape(self.image)[0] / self.live_subsampling),
                                     int(np.shape(self.image)[1] / self.live_subsampling)))

    def scale_image_intensity(self):
        """
        #  Scale the data to the min/max counts, and adjust bit-depth.
        """
        if self.autoscale is True:
            self.max_counts = np.max(self.image)
            self.min_counts = np.min(self.image)
            scaling_factor = 1
            self.image = scaling_factor * ((self.image - self.min_counts) / (self.max_counts - self.min_counts))
        else:
            self.update_min_max_counts()
            scaling_factor = 1
            self.image = scaling_factor * ((self.image - self.min_counts) / (self.max_counts - self.min_counts))
            self.image[self.image < 0] = 0
            self.image[self.image > scaling_factor] = scaling_factor

    def populate_image(self):
        """
        Converts and image to an ImageTk.PhotoImage and populates the Tk Canvas
        """
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(self.cross_hair_image.astype(np.uint8)))
        self.canvas.create_image(0, 0, image=self.tk_image, anchor='nw')

    def display_image(self, image):
        """
        #  Displays a camera image using the Lookup Table specified in the View.
        #  If Autoscale is selected, automatically calculates the min and max values for the data.
        #  If Autoscale is not selected, takes the user values as specified in the min and max counts.
        """
        # Place image in memory
        self.image = image

        # Detect saturated pixels
        self.detect_saturation()
        
        # Down-sample Image for display
        self.downsample_image()

        # Scale image to [0, 1] values
        self.scale_image_intensity()

        #  Update the GUI according to the instantaneous or rolling average max counts.
        self.update_max_counts()

        # Add Cross-Hair
        self.add_crosshair()

        #  Apply Lookup Table
        self.apply_LUT()

        # Create ImageTk.PhotoImage
        self.populate_image()

        # Update Channel Index
        # self.image_metrics['Channel'].set(self.parent_controller.model.return_channel_index())

        # Iterate Image Count for Rolling Average
        self.image_count = self.image_count + 1

    def add_crosshair(self):
        """ Adds a cross-hair to the image.

        Params
        -------
        self.image : np.array
            Must be a 2D image.

        Returns
        -------
        self.apply_cross_hair_image : np.arrays
            2D image, scaled between 0 and 1 with cross-hair if self.apply_cross_hair == True
        """
        self.cross_hair_image = np.copy(self.image)
        if self.apply_cross_hair:
            (height, width) = np.shape(self.image)
            height = int(np.floor(height / 2))
            width = int(np.floor(width / 2))
            self.cross_hair_image[:, width] = 1
            self.cross_hair_image[height, :] = 1

    def apply_LUT(self):
        """
        Applies a LUT to the image.
        Red is reserved for saturated pixels.
        self.color_values = ['gray', 'gradient', 'rainbow']
        """
        if self.colormap == 'gradient':
            self.cross_hair_image = self.rainbow_lut(self.cross_hair_image)
        elif self.colormap == 'rainbow':
            self.cross_hair_image = self.gradient_lut(self.cross_hair_image)
        else:
            self.cross_hair_image = self.gray_lut(self.cross_hair_image)

        # Convert RGBA to RGB Image.
        self.cross_hair_image = self.cross_hair_image[:, :, :3]

        # Specify the saturated values in the red channel
        if np.any(self.saturated_pixels):
            # Saturated pixels is an array of True False statements same size as the image.
            # Pull out the red image from the RGBA, set saturated pixels to 1, put back into array.
            red_image = self.cross_hair_image[:, :, 2]
            red_image[self.saturated_pixels] = 1
            self.cross_hair_image[:, :, 2] = red_image

        # Scale back to an 8-bit image.
        self.cross_hair_image = self.cross_hair_image * (2 ** self.bit_depth - 1)

    def update_LUT(self):
        """
        # When the LUT is changed in the GUI, this function is called.
        # Updates the LUT.
        """
        if self.image is None:
            pass
        else:
            self.colormap = self.view.scale_palette.color.get()
            self.add_crosshair()
            self.apply_LUT()
            self.populate_image()
            logger.debug(f"Updating the LUT, {self.colormap}")

    def detect_saturation(self):
        """
        Looks for any pixels at the maximum intensity allowable for the camera.
        """
        saturation_value = 2**16-1
        self.saturated_pixels = self.image[self.image > saturation_value]

    def toggle_min_max_buttons(self):
        """
        Checks the value of the autoscale widget.
        If enabled, the min and max widgets are disabled and the image intensity is autoscaled.
        If disabled, miu and max widgets are enabled, and image intensity scaled.
        """
        self.autoscale = self.image_palette['Autoscale'].get()
        if self.autoscale is True:  # Autoscale Enabled
            self.image_palette['Min'].widget['state'] = 'disabled'
            self.image_palette['Max'].widget['state'] = 'disabled'
            if self.verbose:
                print("Autoscale Enabled")
            logger.debug("Autoscale Enabled")

        elif self.autoscale is False:  # Autoscale Disabled
            self.image_palette['Min'].widget['state'] = 'normal'
            self.image_palette['Max'].widget['state'] = 'normal'
            if self.verbose:
                print("Autoscale Disabled")
            logger.debug("Autoscale Disabled")
            self.update_min_max_counts()

    def update_min_max_counts(self):
        """
        When the min and max counts are toggled in the GUI, this function is called.
        Updates the min and max values.
        """
        self.min_counts = self.image_palette['Min'].get()
        self.max_counts = self.image_palette['Max'].get()
        if self.verbose:
            print("Min and Max counts scaled to ", self.min_counts, self.max_counts)
        logger.debug(f"Min and Max counts scaled to, {self.min_counts}, {self.max_counts}")

