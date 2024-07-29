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

# Standard Library Imports
import platform
import tkinter as tk
import logging
import threading

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

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ABaseViewController(metaclass=ABCMeta):
    """Abstract Base View Controller Class."""

    def __init__(self):
        pass

    def update_snr(self):
        """Updates the signal to noise ratio."""
        pass

    def initialize(self):
        """Initializes the camera view controller."""
        pass

    def set_mode(self, mode=""):
        """Sets mode of camera_view_controller."""
        pass

    def initialize_non_live_display(self, buffer, microscope_state, camera_parameters):
        """Initialize the non-live display."""
        pass

    def try_to_display_image(self, image_id):
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

        #: SharedNDArray: The shared array that contains the image data.
        self.data_buffer = None

        #: VariableWithLock: The variable that indicates if the image is being
        # displayed.
        self.is_displaying_image = VariableWithLock(bool)

        #: logging.Logger: The logger for the camera view controller.
        self.logger = logging.getLogger(p)

        #: int: Number of images received.
        self.image_count = 0

        #: int: Index of the slice.
        self.slice_index = 0

        #: str: The stack cycling mode.
        self.stack_cycling_mode = "per_stack"

        #: int: Number of channels.
        self.number_of_channels = 0

        #: int: Number of slices.
        self.number_of_slices = 0

        #: int: Total number of images per volume.
        self.total_images_per_volume = 0

        #: int: The original image height.
        self.original_image_height = 2048  # 2014

        #: int: The original image width.
        self.original_image_width = 2048  # 2014

        #: bool: Flat to flip the camera
        self.flip_flags = None

        #: int: The canvas width.
        self.canvas_width = 512

        #: int: The canvas height.
        self.canvas_height = 512

        #: int: The zoom width.
        self.zoom_width = self.canvas_width

        #: int: The zoom height.
        self.zoom_height = self.canvas_height

        #: numpy.ndarray: The zoom rectangle.
        self.zoom_rect = np.array([[0, self.canvas_width], [0, self.canvas_height]])

        #: numpy.ndarray: The zoom offset.
        self.zoom_offset = np.array([[0], [0]])

        #: float: The zoom value.
        self.zoom_value = 1

        #: float: The zoom scale.
        self.zoom_scale = 1

        #: float: The canvas width scale.
        self.canvas_width_scale = 1

        #: float: The canvas height scale.
        self.canvas_height_scale = 1

        #: bool: The crosshair flag.
        self.apply_cross_hair = True

        #: event: The resize event id.
        self.resize_event_id = None

        #: tkinter.Canvas: The tkinter canvas that displays the image.
        self.canvas = self.view.canvas

    def try_to_display_image(self, image_id):
        """Try to display an image.

        Parameters
        ----------
        image_id : int
            Frame index in the data_buffer.
        """
        with self.is_displaying_image as is_displaying_image:
            if is_displaying_image.value:
                return
            is_displaying_image.value = True

        display_thread = threading.Thread(target=self.display_image, args=(image_id,))
        display_thread.start()

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
        if self.stack_cycling_mode == "per_stack":
            for i in range(self.number_of_channels):
                if (
                    i * self.number_of_slices
                    <= self.image_count
                    < (i + 1) * self.number_of_slices
                ):
                    channel_idx = i
                    slice_idx = self.image_count - i * self.number_of_slices
                    break

        elif self.stack_cycling_mode == "per_z":
            # Every image that comes in will be the next channel.
            channel_idx = self.image_count % self.number_of_channels
            slice_idx = self.image_count // self.number_of_channels

        self.image_count += 1
        return channel_idx, slice_idx

    def initialize_non_live_display(self, buffer, microscope_state, camera_parameters):
        """Initialize the non-live display.

        Starts image and slice counter, number of channels, number of slices,
        images per volume, and image volume.

        Parameters
        ----------
        buffer : numpy.ndarray
            Image data.
        microscope_state : dict
            Microscope state.
        camera_parameters : dict
            Camera parameters.
        """
        self.data_buffer = buffer
        self.is_displaying_image.value = False
        self.image_count = 0  # was image_counter
        self.slice_index = 0

        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        self.number_of_channels = int(microscope_state["selected_channels"])
        self.number_of_slices = int(microscope_state["number_z_steps"])
        self.total_images_per_volume = self.number_of_channels * self.number_of_slices
        self.original_image_width = int(camera_parameters["x_pixels"])
        self.original_image_height = int(camera_parameters["y_pixels"])

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

    def left_click(self, event):
        """Toggles cross-hair on image upon left click event.

        Parameters
        ----------
        event : tkinter.Event
            Tkinter event.
        """
        if self.image is not None:
            self.apply_cross_hair = not self.apply_cross_hair
            image = self.add_crosshair(image=self.image)
            image = self.apply_LUT(image=image)
            self.populate_image(image=image)

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

        #: dict: The dictionary of image metrics widgets.
        self.image_metrics = view.image_metrics.get_widgets()

        #: bool: The signal to noise ratio flag.
        self._snr_selected = False

        #: dict: The dictionary of image palette widgets.
        self.image_palette = view.scale_palette.get_widgets()

        # Bindings for changes to the LUT
        for color in self.image_palette.values():
            color.widget.config(command=self.update_LUT)
        self.update_snr()

        # Binding for adjusting the lookup table min and max counts.
        # keys = ['Autoscale', 'Min','Max']
        self.image_palette["Min"].widget.config(command=self.update_min_max_counts)
        self.image_palette["Max"].widget.config(command=self.update_min_max_counts)
        self.image_palette["Autoscale"].widget.config(
            command=self.toggle_min_max_buttons
        )

        # Transpose and live bindings
        self.image_palette["Flip XY"].widget.config(command=self.transpose_image)
        self.view.live_frame.live.bind(
            "<<ComboboxSelected>>", self.update_display_state
        )

        #: event: The resize event id.
        self.resize_event_id = None
        if platform.system() == "Windows":
            self.resize_event_id = self.view.bind("<Configure>", self.resize)

        #: int: The width of the canvas.
        #: int: The height of the canvas.
        self.width, self.height = 663, 597
        self.canvas_width, self.canvas_height = (
            self.view.canvas_width,
            self.view.canvas_height,
        )
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

        #: numpy.ndarray: The image data.
        self.tk_image = None

        #: numpy.ndarray: The image data.
        self.image = None

        #: numpy.ndarray: The image data.
        self.cross_hair_image = None

        #: numpy.ndarray: The image data.
        self.saturated_pixels = None

        #: numpy.ndarray: The image data.
        self.down_sampled_image = None

        #: numpy.ndarray: The image data.
        self.zoom_image = None

        #: bool: The autoscale flag.
        self.autoscale = True

        #: int: The maximum image counts.
        self.max_counts = None

        #: int: The minimum image counts.
        self.min_counts = None

        #: bool: The crosshair flag.
        self.apply_cross_hair = True

        #: str: The mode of the camera view controller.
        self.mode = "stop"

        #: bool: The transpose flag.
        self.transpose = False

        #: str: The display state.
        self.display_state = "Live"

        # Colormap Information
        #: matplotlib.colors.LinearSegmentedColormap: The colormap.
        self.colormap = plt.get_cmap("gist_gray")

        #: int: The number of images displayed.
        self.image_count = 0

        #: ndarray: A temporary array for image processing.
        self.temp_array = None

        #: int: The number of frames to average.
        self.rolling_frames = 1

        #: list: The list of maximum intensity values.
        self.max_intensity_history = []

        #: int: The bit-depth for PIL presentation.
        self.bit_depth = 8

        #: int: The canvas width scaling factor.
        self.canvas_width_scale = 4

        #: int: The canvas height scaling factor.
        self.canvas_height_scale = 4

        #: int: The number of slices.
        self.number_of_slices = 0

        #: numpy.ndarray: The image volume.
        self.image_volume = None

        #: int: The total number of images per volume.
        self.total_images_per_volume = 0

        #: int: The number of channels.
        self.number_of_channels = 0

        #: int: The image counter.
        self.image_counter = 0

        #: int: The slice index.
        self.slice_index = 0

        #: int: The channel index.
        self.channel_index = 0

        #: bool: The display mask flag.
        self.mask_color_table = None

        #: bool: Whether or not to flip the image.
        self.flip_flags = None

        #: bool: Image catche flag
        self.image_catche_flag = True

        # ilastik mask
        #: bool: The display mask flag for ilastik.
        self.display_mask_flag = False

        #: threading.Lock: The lock for the ilastik mask.
        self.ilastik_mask_ready_lock = threading.Lock()

        #: numpy.ndarray: The ilastik mask.
        self.ilastik_seg_mask = None

    def update_snr(self):
        """Updates the signal to noise ratio."""
        #: bool: The signal to noise ratio flag.
        self._snr_selected = False
        #: numpy.ndarray: The offset of the image.
        #: numpy.ndarray: The variance of the image.
        self._offset, self._variance = None, None
        off, var = self.parent_controller.model.get_offset_variance_maps()
        if off is None:
            self.image_palette["SNR"].grid_remove()
        else:
            self._offset, self._variance = copy.deepcopy(off), copy.deepcopy(var)
            self.image_palette["SNR"].grid(row=3, column=0, sticky=tk.NSEW, pady=3)

    def slider_update(self, event):
        """Updates the image when the slider is moved.

        Parameters
        ----------
        event : tkinter event
            The tkinter event that triggered the function.
        """

        slider_index = self.view.slider.get()
        channel_display_index = 0
        self.retrieve_image_slice_from_volume(
            slider_index=slider_index, channel_display_index=channel_display_index
        )
        self.reset_display()

    def update_display_state(self, event):
        """Image Display Combobox Called.

        Sets self.display_state to desired display format.
        Toggles state of slider widget.
        Sets number of positions.

        Parameters
        ----------
        event : tkinter event
            The tkinter event that triggered the function.
        """
        self.display_state = self.view.live_frame.live.get()
        # Slice in the XY Dimension.
        if self.display_state == "XY Slice":
            print("XY Slice")
            try:
                slider_length = np.shape(self.image_volume)[2] - 1
            except IndexError:
                slider_length = (
                    self.parent_controller.configuration["experiment"][
                        "MicroscopeState"
                    ]["number_z_steps"]
                    - 1
                )
        if self.display_state == "YZ Slice":
            try:
                slider_length = np.shape(self.image_volume)[0] - 1
            except IndexError:
                slider_length = (
                    self.parent_controller.configuration["experiment"][
                        "CameraParameters"
                    ]["y_pixels"]
                    - 1
                )
        if self.display_state == "YZ Slice":
            try:
                slider_length = np.shape(self.image_volume)[1] - 1
            except IndexError:
                slider_length = (
                    self.parent_controller.configuration["experiment"][
                        "CameraParameters"
                    ]["x_pixels"]
                    - 1
                )

        if self.display_state.find("Slice") != -1:
            self.view.slider.slider_widget.configure(
                to=slider_length, tickinterval=(slider_length / 5), state="normal"
            )
        else:
            self.view.slider.slider_widget.configure(state="disabled")

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
        # Pallete section (colors, autoscale, min/max counts)
        # keys = ['Frames to Avg', 'Image Max Counts', 'Channel']
        if name == "minmax":
            min = data[0]
            max = data[1]

            # Invoking defaults
            self.image_palette["Gray"].widget.invoke()
            self.image_palette["Autoscale"].widget.invoke()

            # Populating defaults
            self.image_palette["Min"].set(min)
            self.image_palette["Max"].set(max)
            self.image_palette["Min"].widget["state"] = "disabled"
            self.image_palette["Max"].widget["state"] = "disabled"

        self.image_palette["Flip XY"].widget.invoke()

        # Image Metrics section
        if name == "image":
            frames = data[0]
            # Populating defaults
            self.image_metrics["Frames"].set(frames)

    #  Set mode for the execute statement in main controller

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

    def process_image(self):
        """Process the image to be displayed.

        Applies digital zoom, detects saturation, down-samples the image, scales the
        image intensity, adds a crosshair, applies the lookup table, and populates the
        image.
        """
        image = self.digital_zoom()
        self.detect_saturation(image)
        image = self.down_sample_image(image)
        image = self.scale_image_intensity(image)
        image = self.add_crosshair(image)
        image = self.apply_LUT(image)
        self.populate_image(image)

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

        image = (image - self.min_counts) / (self.max_counts - self.min_counts)
        image[image < 0] = 0
        image[image > 1] = 1
        return image

    def populate_image(self, image):
        """Converts image to an ImageTk.PhotoImage and populates the Tk Canvas"""
        if self.display_mask_flag:
            self.ilastik_mask_ready_lock.acquire()
            temp_img1 = image.astype(np.uint8)
            img1 = Image.fromarray(temp_img1)

            temp_img2 = cv2.resize(self.ilastik_seg_mask, temp_img1.shape[:2])
            img2 = Image.fromarray(temp_img2)
            temp_img = Image.blend(img1, img2, 0.2)
        else:
            temp_img = Image.fromarray(image.astype(np.uint8))

        # when calling ImageTk.PhotoImage() to generate a new image, it will destroy
        # what the canvas is showing and cause a blink.
        if self.image_catche_flag:
            self.tk_image = ImageTk.PhotoImage(temp_img)
            self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        else:
            self.tk_image2 = ImageTk.PhotoImage(temp_img)
            self.canvas.create_image(0, 0, image=self.tk_image2, anchor="nw")

        self.image_catche_flag = not self.image_catche_flag

    def retrieve_image_slice_from_volume(self, slider_index, channel_display_index):
        """Retrieve image slice from volume.

        Parameters
        ----------
        slider_index : int
            Index of the slider.
        channel_display_index : int
            Index of the channel to display.
        """
        if self.display_state == "XY MIP":
            self.image = np.max(
                self.image_volume[:, :, :, channel_display_index], axis=2
            )
        if self.display_state == "YZ MIP":
            self.image = np.max(
                self.image_volume[:, :, :, channel_display_index], axis=0
            )
        if self.display_state == "ZY MIP":
            self.image = np.max(
                self.image_volume[:, :, :, channel_display_index], axis=1
            )
        if self.display_state == "XY Slice":
            self.image = self.image_volume[:, :, slider_index, channel_display_index]
        if self.display_state == "YZ Slice":
            self.image = self.image_volume[slider_index, :, :, channel_display_index]
        if self.display_state == "ZY Slice":
            self.image = self.image_volume[:, slider_index, :, channel_display_index]

    def display_image(self, image_id):
        """Display an image using the LUT specified in the View.

        If Autoscale is selected, automatically calculates
        the min and max values for the data.

        If Autoscale is not selected, takes the user values
        as specified in the min and max counts.

        Parameters
        ----------
        image_id: int
            frame index in the data_buffer.
        """

        # Store the maximum intensity value for the image.
        image = self.data_buffer[image_id]
        # flip back image
        if self.flip_flags["x"] and self.flip_flags["y"]:
            image = image[::-1, ::-1]
        elif self.flip_flags["x"]:
            image = image[:, ::-1]
        elif self.flip_flags["y"]:
            image = image[::-1, :]

        self.max_intensity_history.append(np.max(image))

        # If the user has toggled the transpose button, transpose the image.
        if self.transpose:
            self.image = image.T
        else:
            self.image = image

        if self._snr_selected:
            self.image = compute_signal_to_noise(
                self.image, self._offset, self._variance
            )

        # MIP and Slice Mode TODO: Consider channels
        # if self.display_state != 'Live':
        #     slider_index = self.view.slider.slider_widget.get()
        #     channel_display_index = 0
        #     self.retrieve_image_slice_from_volume(slider_index=slider_index,
        #                                           channel_display_index=channel_display_index)
        #
        # else:
        self.process_image()
        self.update_max_counts()
        self.image_metrics["Channel"].set(self.channel_index)
        self.image_count = self.image_count + 1
        with self.is_displaying_image as is_displaying_image:
            is_displaying_image.value = False

    def add_crosshair(self, image):
        """Adds a cross-hair to the image."""
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
        else:
            return image

    def apply_LUT(self, image):
        """Applies a LUT to an image.

        Red is reserved for saturated pixels.
        self.color_values = ['gray', 'gradient', 'rainbow']
        """
        image = self.colormap(image)

        # Convert RGBA to RGB Image.
        image = image[:, :, :3]

        # Specify the saturated values in the red channel
        if np.any(self.saturated_pixels):
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

    def update_LUT(self):
        """Update the LUT in the Camera View.

        When the LUT is changed in the GUI, this function is called.
        Updates the LUT.

        Parameters
        ----------
        self.image : np.array
            Must be a 2D image.

        Returns
        -------
        self.apply_LUT_image : np.arrays
        """
        if self.image is None:
            pass
        else:
            cmap_name = self.view.scale_palette.color.get()
            self._snr_selected = (
                True if cmap_name == "RdBu_r" else False
            )  # TODO: Don't use a proxy for SNR
            self.colormap = plt.get_cmap(cmap_name)
            image = self.add_crosshair(image=self.image)
            image = self.apply_LUT(image=image)
            self.populate_image(image=image)
            logger.debug(f"Updating the LUT, {cmap_name}")

    def detect_saturation(self, image):
        """Look for any pixels at the maximum intensity allowable for the camera."""
        saturation_value = 2**16 - 1
        self.saturated_pixels = image[image > saturation_value]

    def toggle_min_max_buttons(self):
        """Checks the value of the autoscale widget.

        If enabled, the min and max widgets are disabled and the image intensity is
        autoscaled. If disabled, miu and max widgets are enabled, and image intensity
        scaled.
        """
        self.autoscale = self.image_palette["Autoscale"].get()

        if self.autoscale is True:  # Autoscale Enabled
            self.image_palette["Min"].widget["state"] = "disabled"
            self.image_palette["Max"].widget["state"] = "disabled"
            logger.info("Autoscale Enabled")

        elif self.autoscale is False:  # Autoscale Disabled
            self.image_palette["Min"].widget["state"] = "normal"
            self.image_palette["Max"].widget["state"] = "normal"
            logger.info("Autoscale Disabled")
            self.update_min_max_counts()

    def transpose_image(self):
        """Get Flip XY widget value from the View.

        If True, transpose the image.

        Returns
        -------
        self.image : np.array
            Transposed image.
        """
        self.transpose = self.image_palette["Flip XY"].get()

    def update_min_max_counts(self):
        """Get min and max count values from the View.

        When the min and max counts are toggled in the GUI, this function is called.
        Updates the min and max values.

        Returns
        -------
        self.min_counts : int
            Minimum counts for the image.
        self.max_counts : int
            Maximum counts for the image.
        """
        if self.image_palette["Min"].get() != "":
            self.min_counts = float(self.image_palette["Min"].get())
        if self.image_palette["Max"].get() != "":
            self.max_counts = float(self.image_palette["Max"].get())
        logger.debug(
            f"Min and Max counts scaled to, {self.min_counts}, {self.max_counts}"
        )

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
        self.zx_mip = None
        self.zy_mip = None
        self.xy_mip = None

    def preallocate_matrices(self):
        """Preallocate the matrices for the MIP."""

        self.xy_mip = np.zeros(
            (
                self.number_of_channels,
                self.original_image_height,
                self.original_image_width,
            ),
            dtype=np.uint16,
        )

        self.zy_mip = np.zeros(
            (
                self.number_of_channels,
                self.number_of_slices,
                self.original_image_width,
            ),
            dtype=np.uint16,
        )

        self.zx_mip = np.zeros(
            (
                self.number_of_channels,
                self.number_of_slices,
                self.original_image_height,
            ),
            dtype=np.uint16,
        )

    def try_to_display_image(self, image_id):
        """Display the image.

        Parameters
        ----------
        image_id : int
            The image id.
        """
        channel_idx, slice_idx = self.identify_channel_index_and_slice()

        image = self.data_buffer[image_id]

        print("Image size!", image.shape)

        # Take maximum of the current image and the MIP image.
        self.xy_mip[channel_idx] = np.maximum(self.xy_mip[channel_idx], image)

        self.populate_image(self.xy_mip[channel_idx])

    def populate_image(self, image):
        """Converts image to an ImageTk.PhotoImage and populates the Tk Canvas"""
        temp_img = Image.fromarray(image.astype(np.uint8))
        tk_image = ImageTk.PhotoImage(temp_img)
        self.canvas.create_image(0, 0, image=tk_image, anchor="nw")
