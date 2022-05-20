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

from controller.sub_controllers.gui_controller import GUI_Controller
import tkinter as tk
import numpy as np
import cv2
from PIL import Image, ImageTk
from skimage.color import convert_colorspace


class Camera_View_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # Getting Widgets/Buttons
        self.image_metrics = view.image_metrics.get_widgets()
        self.pallete = view.scale_pallete.get_widgets()

        # Binding for adjusting the lookup table min and max counts.
        # keys = ['Autoscale', 'Min','Max']
        self.pallete['Autoscale'].widget.config(command=self.toggle_min_max_buttons)
        self.pallete['Min'].widget.config(command=self.update_min_max_counts)
        self.pallete['Max'].widget.config(command=self.update_min_max_counts)

        # Bindings for changes to the LUT
        # keys = ['Gray','Gradient','Rainbow']
        self.pallete['Gray'].widget.config(command=self.update_LUT)
        self.pallete['Gradient'].widget.config(command=self.update_LUT)
        self.pallete['Rainbow'].widget.config(command=self.update_LUT)

        #  Starting Mode
        self.img = None
        self.autoscale = True
        self.max_counts = None
        self.min_counts = None
        self.mode = 'stop'
        self.colormap = 'gray'
        self.image_count = 0
        self.temp_array = None
        self.rolling_frames = 1
        self.live_subsampling = self.parent_controller.configuration.CameraParameters[
            'display_live_subsampling']
        self.canvas = self.view.canvas
        self.bit_depth = 8  # bit-depth for PIL presentation.

    def initialize(self, name, data):
        '''
        #### Function that sets widgets based on data given from main controller/config
        '''
        # Pallete section (colors, autoscale, min/max counts)
        # keys = ['Frames to Avg', 'Image Max Counts', 'Channel']
        if name == 'minmax':
            min = data[0]
            max = data[1]

            # Invoking defaults
            self.pallete['Gray'].widget.invoke()
            self.pallete['Autoscale'].widget.invoke()

            # Populating defaults
            self.pallete['Min'].set(min)
            self.pallete['Max'].set(max)
            self.pallete['Min'].widget['state'] = 'disabled'
            self.pallete['Max'].widget['state'] = 'disabled'

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

    def update_max_counts(self, image):
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
                self.temp_array = image
                self.image_metrics['Image'].set(self.max_counts)
            else:
                # Subsequent frames of the rolling average
                self.temp_array = np.dstack((self.temp_array, image))
                if np.shape(self.temp_array)[2] > self.rolling_frames:
                    self.temp_array = np.delete(self.temp_array, 0, 2)

                # Update GUI
                self.image_metrics['Image'].set(np.max(self.temp_array))

                if self.verbose:
                    print("Rolling Average: ", self.image_count, self.rolling_frames)

    def display_image(self, image):
        """
        #  Displays a camera image using the Lookup Table specified in the View.
        #  If Autoscale is selected, automatically calculates the min and max values for the data.
        #  If Autoscale is not selected, takes the user values as specified in the min and max counts.
        """
        #  Update the GUI according to the instantaneous or rolling average max counts.
        self.update_max_counts(image)

        #  Down-sample the data according to the configuration file.
        if self.live_subsampling != 1:
            image = cv2.resize(image,
                               (int(np.shape(image)[0] / self.live_subsampling),
                                int(np.shape(image)[1] / self.live_subsampling)))

        #  Look for Saturated Pixels
        saturated_pixels = self.detect_saturation(image)

        #  Scale the data to the min/max counts, and adjust bit-depth.
        if self.autoscale is True:
            self.max_counts = np.max(image)
            self.min_counts = np.min(image)
            scaling_factor = 2 ** self.bit_depth
            image = scaling_factor * ((image - self.min_counts) / (self.max_counts - self.min_counts))
        else:
            self.update_min_max_counts()
            scaling_factor = 2 ** self.bit_depth
            image = scaling_factor * ((image - self.min_counts) / (self.max_counts - self.min_counts))
            image[image < 0] = 0
            image[image > scaling_factor] = scaling_factor

        #  Apply Lookup Table
        image = self.apply_LUT(image, saturated_pixels)

        #  Display Image
        self.img = ImageTk.PhotoImage(Image.fromarray(np.uint8(image)))
        self.canvas.create_image(0,
                                 0,
                                 image=self.img,
                                 anchor='nw')

        # Update Channel Index
        self.image_metrics['Channel'].set(self.parent_controller.model.return_channel_index())

        # Iterate Image Count for Rolling Average
        self.image_count = self.image_count + 1

    def update_LUT(self):
        """
        # When the LUT is changed in the GUI, this function is called.
        # Updates the LUT.
        """
        if self.img is None:
            pass
        else:
            self.colormap = self.view.scale_pallete.color.get()
            if self.verbose:
                print("Updating the LUT", self.colormap)
        # self.canvas.create_image(0,
        #                          0,
        #                          image=self.img,
        #                          anchor='nw')

    def toggle_min_max_buttons(self):
        """
        Checks the value of the autoscale widget.
        If enabled, the min and max widgets are disabled and the image intensity is autoscaled.
        If disabled, miu and max widgets are enabled, and image intensity scaled.
        """
        self.autoscale = self.pallete['Autoscale'].get()
        if self.autoscale is True:  # Autoscale Enabled
            self.pallete['Min'].widget['state'] = 'disabled'
            self.pallete['Max'].widget['state'] = 'disabled'
            if self.verbose:
                print("Autoscale Enabled")

        elif self.autoscale is False:  # Autoscale Disabled
            self.pallete['Min'].widget['state'] = 'normal'
            self.pallete['Max'].widget['state'] = 'normal'
            if self.verbose:
                print("Autoscale Disabled")
            self.update_min_max_counts()

    def update_min_max_counts(self):
        """
        When the min and max counts are toggled in the GUI, this function is called.
        Updates the min and max values.
        """
        self.min_counts = self.pallete['Min'].get()
        self.max_counts = self.pallete['Max'].get()
        if self.verbose:
            print("Min and Max counts scaled to ", self.min_counts, self.max_counts)

    def apply_LUT(self, image, saturated_pixels):
        """
        Applies a LUT to the image.
        Red is reserved for saturated pixels.
        """
        # Get the LUT
        self.update_LUT()

        # Create the RGB array
        y, x = np.shape(image)
        image_lut = np.zeros((y, x, 3))

        # Specify the saturated values in the red channel
        if np.any(saturated_pixels):
            saturated_pixels[saturated_pixels] = 2 ** self.bit_depth
            image_lut[:, :, 0] = saturated_pixels

        # Many of the LUTs are not actually implemented in the GUI.
        if self.colormap == 'gray':
            image_lut = image
        elif self.colormap == 'green':
            image_lut[:, :, 1] = image
        elif self.colormap == 'blue':
            image_lut[:, :, 2] = image
        elif self.colormap == 'cyan':
            image_lut[:, :, 1] = image
            image_lut[:, :, 2] = image
        elif self.colormap == 'magenta':
            image_lut[:, :, 0] = image
            image_lut[:, :, 2] = image
        elif self.colormap == 'yellow':
            image_lut[:, :, 0] = image
            image_lut[:, :, 1] = image
        elif self.colormap == 'hot':
            image_lut = convert_colorspace()

        elif self.colormap == 'viridis':
            pass
        else:
            print("Lookup Table Not Implemented in Camera_View_Controller. Displaying as Grayscale.")
            image_lut = image

        return image_lut

    def detect_saturation(self, image):
        """
        Looks for any pixels at the maximum intensity allowable for the camera.
        """
        saturation_value = 2**16-1
        saturated_pixels = image[image > saturation_value]
        return saturated_pixels
