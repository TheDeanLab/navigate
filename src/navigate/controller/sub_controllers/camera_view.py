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

# Standard Library Imports
import platform
import tkinter as tk
import logging
import threading
from typing import Dict
import tempfile
import os

# Third Party Imports
import cv2
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
import copy
from abc import ABCMeta

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.model.analysis.camera import compute_signal_to_noise
from navigate.tools.common_functions import VariableWithLock
from navigate.tools.file_functions import get_ram_info
from navigate.config import get_navigate_path

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ABaseViewController(metaclass=ABCMeta):
    """Abstract Base View Controller Class."""

    def __init__(self):
        pass

    def update_snr(self):
        """Updates the signal-to-noise ratio."""
        pass

    def initialize(self):
        """Initializes the camera view controller."""
        pass

    def set_mode(self, mode=""):
        """Sets mode of camera_view_controller."""
        pass

    def initialize_non_live_display(self, microscope_state, camera_parameters):
        """Initialize the non-live display."""
        pass

    def try_to_display_image(self, image):
        """Try to display an image."""
        pass


class BaseViewController(GUIController, ABaseViewController):
    """Base View Controller Class."""

    def __init__(self, view, parent_controller=None):
        """Initialize the Camera View Controller Class.

        Parameters
        ----------
        view : tkinter.Frame
            The tkinter frame that contains the widgets.
        parent_controller : Controller
            The parent controller of the camera view controller.
        """
        super().__init__(view, parent_controller)

        #: bool: The flag for the selected signal-to-noise ratio.
        self._snr_selected = False

        #: numpy.ndarray: The offset map.
        self._offset = None

        #: numpy.ndarray: The variance map.
        self._variance = None

        #: bool: The flag for the display of the cross-hair.
        self.apply_cross_hair = True

        #: bool: The flag for autoscaling the image intensity.
        self.autoscale = True

        #: int: The bit depth of the image.
        self.bit_depth = 8

        #: tkinter.Canvas: The tkinter canvas that displays the image.
        self.canvas = self.view.canvas

        #: int: The height of the canvas.
        self.canvas_height = 512

        #: int: The scaling factor for the height of the canvas.
        self.canvas_height_scale = 4

        #: int: The width of the canvas.
        self.canvas_width = 512

        #: int: The scaling factor for the width of the canvas.
        self.canvas_width_scale = 4

        #: str: The colormap for the image.
        self.colormap = plt.get_cmap("gist_gray")

        #: str: The mode of the camera view controller.
        self.mode = "stop"

        #: dict: The flip flags for the camera.
        self.flip_flags = None

        #: int: The height of the image.
        self.height = None

        #: numpy.ndarray: The image data.
        self.image = None

        #: bool: The flag for the image cache.
        self.image_cache_flag = True

        #: int: The count of images.
        self.image_count = 0

        #: VariableWithLock: The lock for displaying the image.
        self.is_displaying_image = VariableWithLock(bool)

        #: logging.Logger: The logger for the camera view controller.
        self.logger = logging.getLogger(p)

        #: int: The maximum counts of the image.
        self.max_counts = None

        #: int: The minimum counts of the image.
        self.min_counts = None

        #: int: The number of channels in the image.
        self.number_of_channels = 0

        #: int: The number of slices in the image volume.
        self.number_of_slices = 0

        #: int: The original height of the image.
        self.original_image_height = 2048

        #: int: The original width of the image.
        self.original_image_width = 2048

        #: event: The resize event ID.
        self.resize_event_id = None

        #: np.ndarray: The saturated pixels in the image.
        self.saturated_pixels = None

        #: list: The selected channels being acquired.
        self.selected_channels = None

        #: int: The index of the slice in the image volume.
        self.slice_index = 0

        #: str: The stack cycling mode.
        self.stack_cycling_mode = "per_stack"

        #: ImageTk.PhotoImage: The tkinter image.
        self.tk_image = None

        #: ImageTk.PhotoImage: The tkinter image 2.
        self.tk_image2 = None

        #: int: The total number of images per volume.
        self.total_images_per_volume = 0

        #: bool: The flag for transposing the image.
        self.transpose = False

        #: int: The width of the canvas.
        self.width = None

        #: float: The zoom scale of the image.
        self.zoom_height = self.canvas_height

        #: numpy.ndarray: The zoom offset of the image.
        self.zoom_offset = np.array([[0], [0]])

        #: numpy.ndarray: The zoom rectangle of the image.
        self.zoom_rect = np.array([[0, self.canvas_width], [0, self.canvas_height]])

        #: float: The zoom scale of the image.
        self.zoom_scale = 1

        #: float: The zoom value of the image.
        self.zoom_value = 1

        #: int: The zoom width of the image.
        self.zoom_width = self.canvas_width

        #: dict: The dictionary of image palette widgets.
        self.image_palette = view.lut.get_widgets()

        # Binding for adjusting the lookup table min and max counts.
        self.image_palette["Min"].get_variable().trace_add(
            "write", lambda *args: self.update_min_max_counts(display=True)
        )
        self.image_palette["Max"].get_variable().trace_add(
            "write", lambda *args: self.update_min_max_counts(display=True)
        )
        self.image_palette["Autoscale"].widget.config(
            command=lambda: self.toggle_min_max_buttons(display=True)
        )

        # Bindings for changes to the LUT
        for color in self.view.lut.color_labels:
            self.image_palette[color].widget.config(
                command=lambda: self.update_lut(self.view.lut)
            )

        # Transpose and live bindings
        self.image_palette["Flip XY"].widget.config(
            command=lambda: self.update_transpose_state(display=True)
        )

    def set_mode(self, mode=""):
        """Sets mode of camera_view_controller.

        Parameters
        ----------
        mode : str
            camera_view_controller mode.
        """
        self.mode = mode

    def flip_image(self, image):
        """Flip the image according to the flip flags.

        Parameters
        ----------
        image : numpy.ndarray
            Image data.

        Returns
        -------
        image : numpy.ndarray
            Flipped and/or transposed image data.
        """
        if self.flip_flags["x"] and self.flip_flags["y"]:
            image = image[::-1, ::-1]
        elif self.flip_flags["x"]:
            image = image[:, ::-1]
        elif self.flip_flags["y"]:
            image = image[::-1, :]

        return image
    
    def transpose_image(self, image):
        """Transpose the image according to the flip flags.

        Parameters
        ----------
        image : numpy.ndarray
            Image data.

        Returns
        -------
        image : numpy.ndarray
            Flipped and/or transposed image data.
        """
        if self.transpose:
            image = image.T
        return image

    def update_lut(self, target):
        """Update the LUT in the Camera View.

        When the LUT is changed in the GUI, this function is called.
        Updates the LUT.
        """
        if self.image is None:
            pass
        else:
            cmap_name = target.color.get()
            self._snr_selected = True if cmap_name == "RdBu_r" else False
            self.colormap = plt.get_cmap(cmap_name)
            self.process_image()
            logger.debug(f"Updating the LUT, {cmap_name}")

    def update_transpose_state(self, display=False):
        """Get Flip XY widget value from the View.

        If True, transpose the image.
        """
        self.transpose = self.image_palette["Flip XY"].get()
        if display and self.image is not None:
            self.image = self.flip_image(self.image)
            self.process_image()

    def toggle_min_max_buttons(self, display=False):
        """Checks the value of the autoscale widget.

        If enabled, the min and max widgets are disabled and the image intensity is
        autoscaled. If disabled, miu and max widgets are enabled, and image intensity
        scaled.
        """
        self.autoscale = self.image_palette["Autoscale"].get()

        if self.autoscale is True:
            self.image_palette["Min"].widget["state"] = "disabled"
            self.image_palette["Max"].widget["state"] = "disabled"
            logger.info("Autoscale Enabled")
            if display and self.image is not None:
                self.process_image()

        elif self.autoscale is False:
            self.image_palette["Min"].widget["state"] = "normal"
            self.image_palette["Max"].widget["state"] = "normal"
            logger.info("Autoscale Disabled")
            self.update_min_max_counts(display=display)

    def try_to_display_image(self, image):
        """Try to display an image.

        Parameters
        ----------
        image : numpy.ndarray
            Image data.
        """
        with self.is_displaying_image as is_displaying_image:
            if is_displaying_image.value:
                return
            is_displaying_image.value = True

        display_thread = threading.Thread(target=self.display_image, args=(image,))
        display_thread.start()

    def apply_lut(self, image):
        """Applies a LUT to an image.

        Red is reserved for saturated pixels.
        self.color_values = ['gray', 'gradient', 'rainbow']

        Parameters
        ----------
        image : numpy.ndarray
            Image data.
        """
        image = self.colormap(image)

        # Convert RGBA to RGB Image.
        image = image[:, :, :3]

        # Specify the saturated values in the red channel
        if np.any(self.saturated_pixels):
            # TODO: Evaluate if this is functional.
            # Saturated pixels is an array of True or
            # False statements same size as the image.

            # Pull out the red image from the RGBA
            # Set saturated pixels to 1, put back into array.
            red_image = image[:, :, 2]
            red_image[self.saturated_pixels] = 1
            image[:, :, 2] = red_image

        # Scale back to an 8-bit image.
        image = image * (2**self.bit_depth - 1)
        return image

    def identify_channel_index_and_slice(self):
        """As images arrive, identify channel index and slice.

        Returns
        -------
        channel_idx : int
            The channel index.
        slice_idx : int
            The slice index.
        """
        # Reset the image count after the full acquisition of an image volume.
        if self.image_count == self.total_images_per_volume:
            self.image_count = 0

        # Store each image to the pre-allocated memory.
        if (
            self.image_mode in ["live", "single"]
            or self.image_mode != "customized"
            and self.stack_cycling_mode == "per_z"
        ):
            # Every image that comes in will be the next channel.
            channel_idx = self.image_count % self.number_of_channels
            slice_idx = self.image_count // self.number_of_channels

        elif self.image_mode != "customized" and self.stack_cycling_mode == "per_stack":
            channel_idx = self.image_count // self.number_of_slices
            slice_idx = self.image_count - channel_idx * self.number_of_slices

        else:
            channel_idx = 0
            slice_idx = self.image_count

        self.image_count += 1
        return channel_idx, slice_idx

    def initialize_non_live_display(self, microscope_state, camera_parameters):
        """Initialize the non-live display.

        Parameters
        ----------
        microscope_state : dict
            Microscope state.
        camera_parameters : dict
            Camera parameters.
        """
        self.is_displaying_image.value = False
        self.image_count = 0  # was image_counter
        self.slice_index = 0

        self.image_mode = microscope_state["image_mode"]
        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        self.number_of_channels = int(microscope_state["selected_channels"])

        self.selected_channels = []
        for channel_name, channel_data in microscope_state["channels"].items():
            if channel_data["is_selected"]:
                channel_idx = channel_name.split("_")[-1]
                self.selected_channels.append(f"CH{channel_idx}")

        self.number_of_slices = int(microscope_state["number_z_steps"])
        self.total_images_per_volume = self.number_of_channels * self.number_of_slices
        self.original_image_width = int(camera_parameters["img_x_pixels"])
        self.original_image_height = int(camera_parameters["img_y_pixels"])

        self.flip_flags = (
            self.parent_controller.configuration_controller.camera_flip_flags
        )

        self.update_canvas_size()
        self.reset_display(False)

    def reset_display(self, display_flag=True):
        """Set the display back to the original digital zoom.

        Parameters
        ----------
        display_flag : bool
        """
        self.zoom_width = self.canvas_width
        self.zoom_height = self.canvas_height
        self.zoom_rect = np.array([[0, self.zoom_width], [0, self.zoom_height]])
        self.zoom_offset = np.array([[0], [0]])
        self.zoom_value = 1
        self.zoom_scale = 1
        if display_flag:
            self.process_image()

    def update_canvas_size(self):
        """Update the canvas size."""
        r_canvas_width = int(self.view.canvas["width"])
        r_canvas_height = int(self.view.canvas["height"])
        img_ratio = self.original_image_width / self.original_image_height
        canvas_ratio = r_canvas_width / r_canvas_height

        if canvas_ratio > img_ratio:
            self.canvas_height = r_canvas_height
            self.canvas_width = int(r_canvas_height * img_ratio)
        else:
            self.canvas_width = r_canvas_width
            self.canvas_height = int(r_canvas_width / img_ratio)

        self.canvas_width_scale = float(self.original_image_width / self.canvas_width)
        self.canvas_height_scale = float(
            self.original_image_height / self.canvas_height
        )

    def digital_zoom(self):
        """Apply digital zoom.

        The x and y positions are between 0
        and the canvas width and height respectively.

        """
        self.zoom_rect = self.zoom_rect - self.zoom_offset
        self.zoom_rect = self.zoom_rect * self.zoom_value
        self.zoom_rect = self.zoom_rect + self.zoom_offset
        self.zoom_offset.fill(0)
        self.zoom_value = 1

        if self.zoom_rect[0][0] > 0 or self.zoom_rect[1][0] > 0:
            self.reset_display(False)

        x_start_index = int(-self.zoom_rect[0][0] / self.zoom_scale)
        x_end_index = int(x_start_index + self.zoom_width)

        y_start_index = int(-self.zoom_rect[1][0] / self.zoom_scale)
        y_end_index = int(y_start_index + self.zoom_height)
        zoom_image = self.image[
            int(y_start_index * self.canvas_height_scale) : int(
                y_end_index * self.canvas_height_scale
            ),
            int(x_start_index * self.canvas_width_scale) : int(
                x_end_index * self.canvas_width_scale
            ),
        ]

        return zoom_image

    def detect_saturation(self, image):
        """Look for any pixels at the maximum intensity allowable for the camera."""
        saturation_value = 2**16 - 1
        self.saturated_pixels = image[image > saturation_value]

    def down_sample_image(self, image):
        """Down-sample the data for image display according to widget size."""
        sx, sy = self.canvas_width, self.canvas_height
        down_sampled_image = cv2.resize(image, (sx, sy))
        return down_sampled_image

    def scale_image_intensity(self, image):
        """Scale the data to the min/max counts, and adjust bit-depth."""
        if self.autoscale is True:
            self.max_counts = np.max(image)
            self.min_counts = np.min(image)
        else:
            self.update_min_max_counts()

        if self.max_counts != self.min_counts:
            image = (image - self.min_counts) / (self.max_counts - self.min_counts)
            image[image < 0] = 0
            image[image > 1] = 1
        return image

    def add_crosshair(self, image):
        """Adds a cross-hair to the image.

        Parameters
        ----------
        image : numpy.ndarray
            Image data.

        Returns
        -------
        image : numpy.ndarray
            Image data with cross-hair.
        """
        if self.apply_cross_hair:
            crosshair_x = (self.zoom_rect[0][0] + self.zoom_rect[0][1]) / 2
            crosshair_y = (self.zoom_rect[1][0] + self.zoom_rect[1][1]) / 2
            if crosshair_x < 0 or crosshair_x >= self.canvas_width:
                crosshair_x = -1
            if crosshair_y < 0 or crosshair_y >= self.canvas_height:
                crosshair_y = -1
            image[:, int(crosshair_x)] = 1
            image[int(crosshair_y), :] = 1
        return image

    def array_to_image(self, image):
        """Convert a numpy array to a PIL Image

        Returns
        -------
        image : Image
            A PIL Image
        """
        return Image.fromarray(image.astype(np.uint8))

    def populate_image(self, image):
        """Converts image to an ImageTk.PhotoImage and populates the Tk Canvas"""
        temp_img = self.array_to_image(image)
        # when calling ImageTk.PhotoImage() to generate a new image, it will destroy
        # what the canvas is showing, causing it to blink.
        if self.image_cache_flag:
            self.tk_image = ImageTk.PhotoImage(temp_img)
            self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        else:
            self.tk_image2 = ImageTk.PhotoImage(temp_img)
            self.canvas.create_image(0, 0, image=self.tk_image2, anchor="nw")

        self.image_cache_flag = not self.image_cache_flag

    def process_image(self):
        """Process the image to be displayed.

        Applies digital zoom, detects saturation, down-samples the image, scales the
        image intensity, adds a crosshair, applies the lookup table, and populates the
        image.
        """
        image = self.digital_zoom()
        self.detect_saturation(image)
        image = self.down_sample_image(image)
        image = self.transpose_image(image)
        image = self.scale_image_intensity(image)
        image = self.add_crosshair(image)
        image = self.apply_lut(image)
        self.populate_image(image)

    def left_click(self, *args):
        """Toggles cross-hair on image upon left click event."""
        if self.image is not None:
            self.apply_cross_hair = not self.apply_cross_hair
            self.process_image()

    def resize(self, event):
        """Resize the window.

        Parameters
        ----------
        event : tkinter.Event
            Tkinter event.
        """
        if self.view.is_popup is False and event.widget != self.view:
            return
        if self.view.is_popup is True and event.widget.widgetName != "toplevel":
            return
        if self.resize_event_id:
            self.view.after_cancel(self.resize_event_id)
        self.resize_event_id = self.view.after(
            1000, lambda: self.refresh(event.width, event.height)
        )

    def refresh(self, width, height):
        """Refresh the window.

        Parameters
        ----------
        width : int
            Width of the window.
        height : int
            Height of the window.
        """
        if width == self.width and height == self.height:
            return
        self.canvas_width = width - self.view.image_metrics.winfo_width() - 24
        self.canvas_height = height - 85
        self.view.canvas.config(width=self.canvas_width, height=self.canvas_height)
        self.view.update_idletasks()

        if self.view.is_popup:
            self.width, self.height = self.view.winfo_width(), self.view.winfo_height()
        else:
            self.width, self.height = width, height

        # if resize the window during acquisition, the image showing should be updated
        self.update_canvas_size()
        self.reset_display(False)

    def update_min_max_counts(self, display=False):
        """Get min and max count values from the View.

        When the min and max counts are toggled in the GUI, this function is called.
        Updates the min and max values.
        """
        if self.image_palette["Min"].get() != "":
            self.min_counts = float(self.image_palette["Min"].get())
        if self.image_palette["Max"].get() != "":
            self.max_counts = float(self.image_palette["Max"].get())
        if display and self.image is not None:
            self.process_image()
        logger.debug(
            f"Min and Max counts scaled to, {self.min_counts}, {self.max_counts}"
        )

    def mouse_wheel(self, event):
        """Digitally zooms in or out on the image upon scroll wheel event.

        Sets the self.zoom_value between 0.05 and 1 in .05 unit steps.

        Parameters
        ----------
        event : tkinter.Event
            num = 4 is zoom out.
            num = 5 is zoom in.
            x, y location.  0,0 is top left corner.
        """
        if event.x >= self.canvas_width or event.y >= self.canvas_height:
            return
        self.zoom_offset = np.array([[int(event.x)], [int(event.y)]])
        delta = 120 if platform.system() != "Darwin" else 1
        threshold = event.delta / delta
        if (event.num == 4) or (threshold > 0):
            # Zoom out event.
            self.zoom_value = 0.95
        if (event.num == 5) or (threshold < 0):
            # Zoom in event.
            self.zoom_value = 1.05

        self.zoom_scale *= self.zoom_value
        self.zoom_width /= self.zoom_value
        self.zoom_height /= self.zoom_value

        if self.zoom_width > self.canvas_width or self.zoom_height > self.canvas_height:
            self.reset_display(False)
        elif self.zoom_width < 5 or self.zoom_height < 5:
            return

        self.process_image()


class CameraViewController(BaseViewController):
    """Camera View Controller Class."""

    def __init__(self, view, parent_controller=None):
        """Initialize the Camera View Controller Class.

        Parameters
        ----------
        view : tkinter.Frame
            The tkinter frame that contains the widgets.
        parent_controller : Controller
            The parent controller of the camera view controller.
        """
        super().__init__(view, parent_controller)

        # SpooledImageLoader: The spooled image loader.
        self.spooled_images = None

        #: dict: The dictionary of image metrics widgets.
        self.image_metrics = view.image_metrics.get_widgets()

        self.update_snr()

        self.view.live_frame.live.bind(
            "<<ComboboxSelected>>", self.update_display_state
        )
        self.view.live_frame.channel.bind(
            "<<ComboboxSelected>>", self.update_display_state
        )
        self.view.live_frame.channel.configure(state="disabled")

        # Slider Binding
        self.view.slider.bind("<Motion>", self.slider_update)

        if platform.system() == "Windows":
            self.resize_event_id = self.view.bind("<Configure>", self.resize)

        self.width, self.height = 663, 597
        self.canvas_width, self.canvas_height = 512, 512

        # Right-Click Binding
        #: tkinter.Menu: The tkinter menu that pops up on right click.
        self.menu = tk.Menu(self.canvas, tearoff=0)
        self.menu.add_command(label="Move Here", command=self.move_stage)
        self.menu.add_command(label="Reset Display", command=self.reset_display)
        self.menu.add_command(label="Mark Position", command=self.mark_position)

        #: int: The x position of the mouse.
        self.move_to_x = None

        #: int: The y position of the mouse.
        self.move_to_y = None

        #: str: The display state.
        self.display_state = "Live"

        #: int: The number of frames to average.
        self.rolling_frames = 1

        #: list: The list of maximum intensity values.
        self.max_intensity_history = []

        #: bool: The flag for displaying the mask.
        self.display_mask_flag = False

        #: bool: The display mask flag.
        self.mask_color_table = None

        #: threading.Lock: The lock for the ilastik mask.
        self.ilastik_mask_ready_lock = threading.Lock()

        #: numpy.ndarray: The ilastik mask.
        self.ilastik_seg_mask = None

    def try_to_display_image(self, image):
        """Try to display an image.

        In the live mode, images are automatically passed to the display function.

        In the slice mode, images are passed to a spooled temporary file. However,
        when the same slice and channel index is acquired again, the image is
        updated. In all other cases, the image is only displayed upon slider events.

        Parameters
        ----------
        image : numpy.ndarray
            Image data.
        """
        # Identify the channel index and slice index, update GUI.
        channel_idx, slice_idx = self.identify_channel_index_and_slice()
        self.image_metrics["Channel"].set(int(self.selected_channels[channel_idx][2:]))

        # Save the image to the spooled image loader.
        self.spooled_images.save_image(
            image=image, channel=channel_idx, slice_index=slice_idx
        )

        # Update image according to the display state.
        self.display_state = self.view.live_frame.live.get()
        if self.display_state == "Live":
            super().try_to_display_image(image)

        elif self.display_state == "Slice":
            requested_slice = self.view.slider.get()
            requested_channel = self.view.live_frame.channel.get()
            requested_channel = int(requested_channel[-1]) - 1
            if slice_idx == requested_slice and channel_idx == requested_channel:
                super().try_to_display_image(image)

    def initialize_non_live_display(self, microscope_state, camera_parameters):
        """Initialize the non-live display.

        Parameters
        ----------
        microscope_state : dict
            Microscope state.
        camera_parameters : dict
            Camera parameters.
        """
        super().initialize_non_live_display(microscope_state, camera_parameters)
        self.update_display_state()
        self.view.live_frame.channel["values"] = self.selected_channels
        self.spooled_images = SpooledImageLoader(
            channels=self.number_of_channels,
            size_y=self.original_image_height,
            size_x=self.original_image_width,
        )

    def update_snr(self):
        """Updates the signal-to-noise ratio."""
        off, var = self.parent_controller.model.get_offset_variance_maps()
        if off is None:
            self.image_palette["SNR"].grid_remove()
        else:
            self._offset, self._variance = copy.deepcopy(off), copy.deepcopy(var)
            self.image_palette["SNR"].grid(row=3, column=0, sticky=tk.NSEW, pady=3)

    def slider_update(self, *args):
        """Updates the image when the slider is moved."""

        slider_index = self.view.slider.get()
        channel_index = self.view.live_frame.channel.get()
        channel_index = channel_index[-1]
        channel_index = int(channel_index) - 1
        image = self.spooled_images.load_image(
            channel=channel_index, slice_index=slider_index
        )

        if image is None:
            return

        self.image = self.flip_image(image)
        self.process_image()
        self.update_max_counts()

        with self.is_displaying_image as is_displaying_image:
            is_displaying_image.value = False

    def update_display_state(self, *args):
        """Image Display Combobox Called.

        Sets self.display_state to desired display format.
        Toggles state of slider widget.
        Sets number of positions.
        """
        if self.number_of_slices == 0:
            return

        self.display_state = self.view.live_frame.live.get()
        if self.display_state == "Live":
            self.view.slider.configure(state="disabled")
            self.view.slider.grid_remove()
            self.view.live_frame.channel.configure(state="disabled")
        else:
            self.view.slider.set(1)
            self.view.slider.configure(
                from_=1,
                to=self.number_of_slices,
                tickinterval=self.number_of_slices // 11,
            )
            self.view.slider.configure(state="normal")
            self.view.slider.grid()
            self.view.live_frame.channel.configure(state="normal")
            if self.view.live_frame.channel.get() not in self.selected_channels:
                self.view.live_frame.channel.set(self.selected_channels[0])

    def get_absolute_position(self):
        """Gets the absolute position of the computer mouse.

        Returns
        -------
        x : int
            The x position of the mouse.
        y : int
            The y position of the mouse.
        """
        x = self.parent_controller.view.winfo_pointerx()
        y = self.parent_controller.view.winfo_pointery()
        return x, y

    def popup_menu(self, event):
        """Right-Click Popup Menu

        Parameters
        ----------
        event : tkinter.Event
            x, y location.  0,0 is top left corner.
        """
        try:
            # only popup the menu when click on image
            if event.x >= self.canvas_width or event.y >= self.canvas_height:
                return
            self.move_to_x = event.x
            self.move_to_y = event.y
            x, y = self.get_absolute_position()
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def initialize(self, name, data):
        """Sets widgets based on data given from main controller/config.

        Parameters
        ----------
        name : str
            'minmax', 'image'.
        data : list
            Min and max intensity values.
        """
        # Pallet section (colors, autoscale, min/max counts)
        # keys = ['Frames to Avg', 'Image Max Counts', 'Channel']
        if name == "minmax":
            min_value = data[0]
            max_value = data[1]

            # Invoking defaults
            self.image_palette["Gray"].widget.invoke()
            self.image_palette["Autoscale"].widget.invoke()

            # Populating defaults
            self.image_palette["Min"].set(min_value)
            self.image_palette["Max"].set(max_value)
            self.image_palette["Min"].widget["state"] = "disabled"
            self.image_palette["Max"].widget["state"] = "disabled"

        self.image_palette["Flip XY"].widget.invoke()

        # Image Metrics section
        if name == "image":
            frames = data[0]
            # Populating defaults
            self.image_metrics["Frames"].set(frames)

    def set_mode(self, mode=""):
        """Sets mode of camera_view_controller.

        Parameters
        ----------
        mode : str
            camera_view_controller mode.
        """
        self.mode = mode
        if mode == "live" or mode == "stop":
            self.menu.entryconfig("Move Here", state="normal")
        else:
            self.menu.entryconfig("Move Here", state="disabled")

    def mark_position(self):
        """Marks the current position of the microscope in
        the multi-position acquisition table."""
        offset_x, offset_y = self.calculate_offset()
        stage_position = self.parent_controller.execute("get_stage_position")
        if stage_position is not None:
            stage_flip_flags = (
                self.parent_controller.configuration_controller.stage_flip_flags
            )
            stage_position["x"] = float(stage_position["x"]) + offset_x * (
                -1 if stage_flip_flags["x"] else 1
            )
            stage_position["y"] = float(stage_position["y"]) - offset_y * (
                -1 if stage_flip_flags["y"] else 1
            )

            # Place the stage position in the multi-position table.
            self.parent_controller.execute("mark_position", stage_position)

    def calculate_offset(self):
        """Calculates the offset of the image.

        Returns
        -------
        offset_x : int
            The offset of the image in x.
        offset_y : int
            The offset of the image in y.
        """
        current_center_x = (self.zoom_rect[0][0] + self.zoom_rect[0][1]) / 2
        current_center_y = (self.zoom_rect[1][0] + self.zoom_rect[1][1]) / 2

        microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]
        zoom_value = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["zoom"]
        pixel_size = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][microscope_name]["zoom"]["pixel_size"][zoom_value]

        offset_x = int(
            (self.move_to_x - current_center_x)
            / self.zoom_scale
            * self.canvas_width_scale
            * pixel_size
        )
        offset_y = int(
            (self.move_to_y - current_center_y)
            / self.zoom_scale
            * self.canvas_height_scale
            * pixel_size
        )

        return offset_x, offset_y

    def move_stage(self):
        """Move the stage according to the position the user clicked."""
        offset_x, offset_y = self.calculate_offset()

        self.show_verbose_info(
            f"Try moving stage by {offset_x} in x and {offset_y} in y"
        )

        stage_position = self.parent_controller.execute("get_stage_position")

        if stage_position is not None:
            # TODO: if show image as what the camera gets(flipped one), the stage
            # moving direction should be decided by stage_flip_flags
            # and camera_flip_flags
            stage_flip_flags = (
                self.parent_controller.configuration_controller.stage_flip_flags
            )
            stage_position["x"] += offset_x * (-1 if stage_flip_flags["x"] else 1)
            stage_position["y"] -= offset_y * (-1 if stage_flip_flags["y"] else 1)
            if self.mode == "stop":
                command = "move_stage_and_acquire_image"
            else:
                command = "move_stage_and_update_info"
            self.parent_controller.execute(command, stage_position)
        else:
            tk.messagebox.showerror(
                title="Warning", message="Can't move to there! Invalid stage position!"
            )

    def update_max_counts(self):
        """Update the max counts in the camera view.

        Function gets the number of frames to average from the VIEW.

        If frames to average == 0 or 1, provides the maximum value from the last
        acquired data.
        """

        # If the array is larger than 32 entries, remove the 0th entry.
        if len(self.max_intensity_history) > (2**5):
            self.max_intensity_history = self.max_intensity_history[1:]

        # Get the number of frames to average from the VIEW
        self.rolling_frames = int(self.image_metrics["Frames"].get())

        # Make sure the array is longer than the number of frames to average.
        if self.rolling_frames > len(self.max_intensity_history):
            self.rolling_frames = len(self.max_intensity_history)
            self.image_metrics["Frames"].set(self.rolling_frames)

        if self.rolling_frames == 0:
            # Cannot average 0 frames. Set to 1, and report max intensity
            self.image_metrics["Frames"].set(1)
            self.image_metrics["Image"].set(f"{self.max_intensity_history[-1]:.0f}")
        elif self.rolling_frames == 1:
            self.image_metrics["Image"].set(f"{self.max_intensity_history[-1]:.0f}")
        elif self.rolling_frames > 1:
            rolling_average = (
                sum(self.max_intensity_history[-self.rolling_frames :])
                / self.rolling_frames
            )
            self.image_metrics["Image"].set(f"{rolling_average:.0f}")

    def array_to_image(self, image):
        """Convert a numpy array to a PIL Image.

        If a color mask is present, it will apply the mask to the image.

        Returns
        -------
        image : Image
            A PIL Image
        """
        if self.display_mask_flag and self.display_state == "Live":
            self.ilastik_mask_ready_lock.acquire()
            temp_img1 = image.astype(np.uint8)
            img1 = Image.fromarray(temp_img1)

            temp_img2 = cv2.resize(self.ilastik_seg_mask, temp_img1.shape[:2])
            img2 = Image.fromarray(temp_img2)
            temp_img = Image.blend(img1, img2, 0.2)
        else:
            temp_img = Image.fromarray(image.astype(np.uint8))
        return temp_img

    def display_image(self, image):
        """Display an image using the LUT specified in the View.

        If Autoscale is selected, automatically calculates
        the min and max values for the data.

        If Autoscale is not selected, takes the user values
        as specified in the min and max counts.

        Parameters
        ----------
        image : numpy.ndarray
            Image data.
        """
        self.image = self.flip_image(image)
        self.max_intensity_history.append(np.max(image))
        if self._snr_selected:
            self.image = compute_signal_to_noise(
                self.image, self._offset, self._variance
            )
        self.process_image()
        self.update_max_counts()
        with self.is_displaying_image as is_displaying_image:
            is_displaying_image.value = False

    def set_mask_color_table(self, colors):
        """Set up segmentation mask color table

        Parameters
        ----------
        colors : list
            List of colors to use for the segmentation mask

        Returns
        -------
        self.mask_color_table : np.array
            Array of colors to use for the segmentation mask
        """
        self.mask_color_table = np.zeros((256, 1, 3), dtype=np.uint8)
        self.mask_color_table[0] = [0, 0, 0]
        for i in range(len(colors)):
            color_hex = colors[i]
            self.mask_color_table[i + 1] = [
                int(color_hex[1:3], 16),
                int(color_hex[3:5], 16),
                int(color_hex[5:], 16),
            ]
        if not self.ilastik_mask_ready_lock.locked():
            self.ilastik_mask_ready_lock.acquire()

    def display_mask(self, mask):
        """Display segmentation mask

        Parameters
        ----------
        mask : np.array
            Segmentation mask to display)
        """
        self.ilastik_seg_mask = cv2.applyColorMap(mask, self.mask_color_table)
        self.ilastik_mask_ready_lock.release()

    @property
    def custom_events(self):
        """dict: Custom events for this controller"""
        return {"ilastik_mask": self.display_mask}


class MIPViewController(BaseViewController):
    """MIP View Controller Class."""

    def __init__(self, view, parent_controller=None):
        """Initialize the MIP View Controller Class.

        Parameters
        ----------
        view : tkinter.Frame
            The tkinter frame that contains the widgets.
        parent_controller : Controller
            The parent controller of the camera view controller.
        """
        super().__init__(view, parent_controller)
        self.view = view
        self.image = None
        self.zx_mip = None
        self.zy_mip = None
        self.xy_mip = None
        self.autoscale = True
        self.perspective = "XY"

        self.render_widgets = self.view.render.get_widgets()

    def initialize(self, name, data):
        """Initialize the MIP view.

        Sets the min and max intensity values for the image.
        Disables the min and max widgets.
        Invokes the gray and autoscale widgets.
        Hides the SNR widget.
        Sets the perspective widget values.
        Sets the perspective widget to XY.
        Sets the channel widget to CH0.

        Parameters
        ----------
        name : str
            'minmax', 'image'.
        data : list
            Min and max intensity values.
        """

        min_value = data[0]
        max_value = data[1]
        self.image_palette["Min"].set(min_value)
        self.image_palette["Max"].set(max_value)
        self.image_palette["Min"].widget["state"] = "disabled"
        self.image_palette["Max"].widget["state"] = "disabled"
        self.image_palette["Gray"].widget.invoke()
        self.image_palette["Autoscale"].widget.invoke()
        self.image_palette["SNR"].grid_remove()
        self.render_widgets["perspective"].widget["values"] = ("XY", "ZY", "ZX")
        self.render_widgets["perspective"].set("XY")
        self.render_widgets["channel"].set("CH1")

        # event binding
        self.render_widgets["perspective"].get_variable().trace_add(
            "write", self.display_mip_image
        )
        self.render_widgets["channel"].get_variable().trace_add(
            "write", self.display_mip_image
        )

    def prepare_mip_view(self):
        """Prepare the MIP view.

        Set the number of channels, number of slices, and the selected channels.
        Pre-allocate the matrices for the MIP.
        """
        self.render_widgets["channel"].widget["values"] = self.selected_channels
        self.preallocate_matrices()

    def preallocate_matrices(self):
        """Preallocate the matrices for the MIP.

        Pre-allocated matrix is shape (number_of_channels, number_of_slices, width)
        """

        self.xy_mip = 100 * np.ones(
            (
                self.number_of_channels,
                self.original_image_height,
                self.original_image_width,
            ),
            dtype=np.uint16,
        )

        self.zy_mip = 100 * np.ones(
            (
                self.number_of_channels,
                self.number_of_slices,
                self.original_image_width,
            ),
            dtype=np.uint16,
        )

        self.zx_mip = 100 * np.ones(
            (
                self.number_of_channels,
                self.number_of_slices,
                self.original_image_height,
            ),
            dtype=np.uint16,
        )

    def get_mip_image(self, channel_idx):
        """Get MIP image according to perspective and channel id
        
        Parameters
        ----------
        channel_idx : int
            channel id
        
        Returns
        -------
        image : numpy.ndarray
            Image data
        """
        if self.xy_mip is None:
            return None
        
        display_mode = self.render_widgets["perspective"].get()
        if display_mode == "XY":
            image = self.xy_mip[channel_idx]
        elif display_mode == "ZY":
            image = self.zy_mip[channel_idx].T
        elif display_mode == "ZX":
            image = self.zx_mip[channel_idx]

        image = self.flip_image(image)
        return image
    
    def initialize_non_live_display(self, microscope_state, camera_parameters):
        """Initialize the non-live display.

        Parameters
        ----------
        microscope_state : dict
            Microscope state.
        camera_parameters : dict
            Camera parameters.
        """
        super().initialize_non_live_display(microscope_state, camera_parameters)
        self.perspective = self.render_widgets["perspective"].get()
        self.XY_image_width = self.original_image_width
        self.XY_image_height = self.original_image_height
        # in microns
        z_range = microscope_state["abs_z_end"] - microscope_state["abs_z_start"]
        # TODO: may stretch by the value of binning.
        self.Z_image_value = self.XY_image_width * camera_parameters["fov_x"] / z_range
        self.prepare_mip_view()
        self.update_perspective()

    def try_to_display_image(self, image):
        """Display the image.

        Parameters
        ----------
        image : numpy.ndarray
            Image data.
        """
        channel_idx, slice_idx = self.identify_channel_index_and_slice()

        # Orthogonal maximum intensity projections.
        self.xy_mip[channel_idx] = np.maximum(self.xy_mip[channel_idx], image)
        self.zy_mip[channel_idx, slice_idx] = np.maximum(
            self.zy_mip[channel_idx, slice_idx], np.max(image, axis=0)
        )
        self.zx_mip[channel_idx, slice_idx] = np.maximum(
            self.zx_mip[channel_idx, slice_idx], np.max(image, axis=1)
        )

        self.image = self.get_mip_image(channel_idx)
        self.process_image()

    def display_mip_image(self, *args):
        """Display MIP image in non-live view"""
        if self.perspective != self.render_widgets["perspective"].get():
            self.update_perspective()
        if self.mode != "stop":
            return
        channel_idx = int(self.render_widgets["channel"].get()[2:]) - 1
        self.image = self.get_mip_image(channel_idx)
        if self.image is not None:
            self.process_image()

    def update_perspective(self, *args, display=False):
        display_mode = self.render_widgets["perspective"].get()
        self.perspective = display_mode
        if display_mode == "XY":
            self.original_image_width = self.XY_image_width
            self.original_image_height = self.XY_image_height
        elif display_mode == "ZY":
            self.original_image_width = self.Z_image_value
            self.original_image_height = self.XY_image_height
        elif display_mode == "ZX":
            self.original_image_width = self.Z_image_value
            self.original_image_height = self.XY_image_width

        self.update_canvas_size()
        self.reset_display(False)


class SpooledImageLoader:
    """A class to lazily load images from disk using a spooled temporary file."""

    def __init__(self, channels: int, size_y: int, size_x: int):
        """Initialize the SpooledImageLoader.

        Parameters
        ----------
        channels : int
            The number of channels.
        """
        #: int: The number of channels.
        self.channels = channels

        #: int: The number of bytes in the image.
        self.n_bytes = None

        #: int: The height of the image.
        self.size_y = size_y

        #: int: The width of the image.
        self.size_x = size_x

        max_size_per_channel = self.get_default_max_size() // self.channels
        default_directory = self.get_default_directory()

        #: Dict[int, tempfile.SpooledTemporaryFile]: The temporary files.
        self.temp_files: Dict[int, tempfile.SpooledTemporaryFile] = {}
        for channel in range(self.channels):
            self.temp_files[channel] = tempfile.SpooledTemporaryFile(
                max_size=max_size_per_channel,
                mode="w+b",
                dir=default_directory,
            )

        logger.info(self.__repr__())

    def __del__(self):
        """Delete the temporary files."""
        if self.temp_files is not None:
            for temp_file in self.temp_files.values():
                temp_file.close()

    def __repr__(self):
        """Return the string representation of the SpooledImageLoader."""
        return (
            f"SpooledImageLoader(channels={len(self.temp_files)}, "
            f"size_y={self.size_y}, "
            f"size_x={self.size_x})"
        )

    @staticmethod
    def get_default_max_size() -> int:
        """Get the default max_size based on the total RAM.

        Returns
        -------
        int
            The default max_size in bytes. By default, half the available RAM.
        """
        total_ram, _ = get_ram_info()
        return total_ram // 2

    @staticmethod
    def get_default_directory() -> str:
        """Get the default directory for storing temporary files.

        Default directory is within the .navigate directory.

        Returns
        -------
        str
            The default directory for storing temporary files.
        """
        base_path = get_navigate_path()
        temp_path = os.path.join(base_path, "temp")
        os.makedirs(temp_path, exist_ok=True)
        return temp_path

    def save_image(self, image: np.ndarray, channel: int, slice_index: int):
        """Save an image to a temporary file.

        Parameters
        ----------
        image : np.ndarray
            The image to save.
        channel : int
            The channel of the image.
        slice_index : int
            The slice index of the image.
        """

        image = image.flatten()

        if self.temp_files[channel].tell() == 0:
            self.n_bytes = image.nbytes

        start_idx, end_idx = self.get_indices(slice_index)
        self.temp_files[channel].seek(start_idx)
        self.temp_files[channel].write(image)

    def load_image(self, channel: int, slice_index: int):
        """Load an image from a temporary file.

        Parameters
        ----------
        channel : int
            The channel of the image.
        slice_index : int
            The slice index of the image.

        Returns
        -------
        np.ndarray or None
            The image data or None if the image could not be loaded.
        """
        start_idx, _ = self.get_indices(slice_index)
        self.temp_files[channel].seek(start_idx)

        try:
            image = np.frombuffer(
                self.temp_files[channel].read(self.n_bytes), dtype=np.uint16
            )
            image = np.copy(image.reshape((self.size_y, self.size_x)))
        except (ValueError, TypeError, AttributeError):
            return None
        return image

    def get_indices(self, slice_index: int):
        """Get the indices of the images stored in the spooled files.

        Parameters
        ----------
        slice_index : int
            The slice index.

        Returns
        -------
        Tuple[int, int]
            The start and end indices of the images.
        """

        start_idx = slice_index * self.n_bytes
        end_idx = start_idx + self.n_bytes
        return start_idx, end_idx
