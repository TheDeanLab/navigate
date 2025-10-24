# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
from tkinter import messagebox
import logging
import threading
import queue
from typing import Dict, Optional
import tempfile
import os
import time
import abc
import copy

# Third Party Imports
import cv2
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.model.analysis.camera import compute_signal_to_noise
from navigate.tools.file_functions import get_ram_info
from navigate.config import get_navigate_path, update_config_dict
from navigate.tools.decorators import performance_monitor

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ABaseViewController(metaclass=abc.ABCMeta):
    """Abstract Base View Controller Class."""

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def update_snr(self):
        """Updates the signal-to-noise ratio."""
        pass

    @abc.abstractmethod
    def initialize(self):
        """Initializes the camera view controller."""
        pass

    @abc.abstractmethod
    def set_mode(self, mode=""):
        """Sets mode of camera_view_controller."""
        pass

    @abc.abstractmethod
    def initialize_non_live_display(self, microscope_state, camera_parameters):
        """Initialize the non-live display."""
        pass

    @abc.abstractmethod
    def try_to_display_image(self, image):
        """Try to display an image."""
        pass


class BaseViewController(GUIController, ABaseViewController):
    """Base View Controller Class."""

    def __init__(self, view, parent_controller=None) -> None:
        """Initialize the Camera View Controller Class.

        Parameters
        ----------
        view : tkinter.Frame
            The tkinter frame that contains the widgets.
        parent_controller : Controller
            The parent controller of the camera view controller.
        """
        super().__init__(view, parent_controller)

        #: float: Max frames per second (0 or None disables throttling)
        self.max_fps: float = 20.0

        #: float: Minimum time between processed frames
        self._min_frame_interval: float = 1.0 / self.max_fps

        #: float: Timestamp of last enqueued frame (perf_counter seconds)
        self._last_enqueue_time: float = 0.0

        #: int: Cached maximum value of the last displayed frame.
        self._last_frame_display_max = 0

        #: tkinter.PhotoImage: The tkinter photo image for the canvas.
        self._photo = None

        #: tkinter.PhotoImage: The buffered tkinter photo image for the canvas.
        self._img_buf = None

        #: bool: The flag for the selected signal-to-noise ratio.
        self._snr_selected = False

        #: numpy.ndarray: The lookup table buffer for the image colormap.
        self._lut_buf = None

        #: numpy.ndarray: The offset map.
        self._offset = None

        #: numpy.ndarray: The variance map.
        self._variance = None

        #: str: The imaging mode.
        self.image_mode = None

        #: bool: The flag for the display of the cross-hair.
        self.apply_cross_hair = True

        #: bool: The flag for autoscaling the image intensity.
        self.autoscale = True

        #: int: The bit depth of the image.
        self.bit_depth = 8

        #: tkinter.Canvas: The tkinter canvas that displays the image.
        self.canvas = self.view.canvas

        #: int: The width of the window
        self.width = 663

        #: int: The height of the window
        self.height = 597

        #: int: The height of the canvas.
        self.canvas_height = 512

        #: int: The scaling factor for the height of the canvas.
        self.canvas_height_scale = 4

        #: int: The width of the canvas.
        self.canvas_width = 512

        #: int: The scaling factor for the width of the canvas.
        self.canvas_width_scale = 4

        #: np.ndarray: Precomputed lookup table for the image colormap.
        self.colormap = np.ascontiguousarray(
            self._generate_lut("gist_gray"), dtype=np.uint8
        )

        #: str: The mode of the camera view controller.
        self.mode = "stop"

        #: str: The microscope name
        self.microscope_name = None

        #: dict: The flip flags for the camera.
        self.flip_flags = None

        #: int: The height of the image.
        self.height = None

        #: numpy.ndarray: The image data.
        self.image = None

        #: int: The count of images.
        self.image_count = 0

        #: logging.Logger: The logger for the camera view controller.
        self.logger = logging.getLogger(p)

        #: queue.Queue: single-slot queue for display frames
        self._disp_q = queue.Queue(maxsize=1)

        #: threading.Thread: single persistent display worker
        self._disp_thread = threading.Thread(target=self._display_worker, daemon=True)
        self._disp_thread.start()

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

        #: list: The selected channels being acquired.
        self.selected_channels = None

        #: int: The index of the slice in the image volume.
        self.slice_index = 0

        #: str: The stack cycling mode.
        self.stack_cycling_mode = "per_stack"

        #: ImageTk.PhotoImage: The tkinter image.
        self.tk_image = None

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

        #: Optional[str]: after() id for debouncing min/max updates
        self._minmax_after_id = None

        # Binding for adjusting the lookup table min and max counts (debounced 100 ms)
        self.image_palette["Min"].get_variable().trace_add(
            "write", self._on_minmax_changed
        )
        self.image_palette["Max"].get_variable().trace_add(
            "write", self._on_minmax_changed
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

        #: int: The x position of the mouse.
        self.move_to_x = None

        #: int: The y position of the mouse.
        self.move_to_y = None

        #: float: Percentage of crosshair in x
        self.crosshair_x = 0.5

        #: float: Percentage of crosshair in y
        self.crosshair_y = 0.5

        #: bool: the flag for offsetting the crosshair
        self.offset_crosshair = False

        # Right-Click Popup Menu
        self.menu = tk.Menu(self.canvas, tearoff=0)
        self.menu.add_command(label="Reset Display", command=self.reset_display)
        self.menu.add_separator()
        self.menu.add_command(label="Toggle Crosshair", command=self.left_click)
        self.menu.add_command(label="Move Crosshair", command=self.move_crosshair)
        self.menu.add_separator()
        self.menu.add_command(label="Move Here", command=self.move_stage)
        self.menu.add_command(label="Mark Position", command=self.mark_position)

    def _on_minmax_changed(self, *args) -> None:
        """Debounce updates to min/max entry changes by 100 ms."""

        # Cancel any pending scheduled update
        if self._minmax_after_id:
            try:
                self.view.after_cancel(self._minmax_after_id)
            except Exception:
                pass
            self._minmax_after_id = None

        # Schedule a new update
        self._minmax_after_id = self.view.after(
            100, lambda: self.update_min_max_counts(display=True)
        )

    def initialize(self, name, data) -> None:
        """Sets widgets based on data given from main controller/config.

        Parameters
        ----------
        name : str
            'minmax', 'image'.
        data : list
            Min and max intensity values.
        """

        pass

    def update_snr(self) -> None:
        """Updates the signal-to-noise ratio."""

        pass

    def set_mode(self, mode: str = "") -> None:
        """Sets mode of camera_view_controller.

        Parameters
        ----------
        mode : str
            camera_view_controller mode.
        """
        self.mode = mode

    def flip_image(self, image: np.ndarray) -> np.ndarray:
        """Flip the image according to the flip flags.

        Parameters
        ----------
        image : np.ndarray
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

    def transpose_image(self, image: np.ndarray) -> np.ndarray:
        """Transpose the image according to the flip flags.

        Parameters
        ----------
        image : np.ndarray
            Image data.

        Returns
        -------
        image : np.ndarray
            Flipped and/or transposed image data.
        """
        if self.transpose:
            image = image.T
        return image

    def update_lut(self, target) -> None:
        """Update the LUT in the Camera View.

        When the LUT is changed in the GUI, this function is called.
        Updates the LUT.
        """
        if self.image is None:
            pass
        else:
            cmap_name = target.color.get()
            self._snr_selected = True if cmap_name == "RdBu_r" else False
            self.colormap = np.ascontiguousarray(
                self._generate_lut(cmap_name), dtype=np.uint8
            )
            self.process_image()
            logger.debug(f"Updating the LUT, {cmap_name}")

    def update_transpose_state(self, display: bool = False) -> None:
        """Get Flip XY widget value from the View.

        If True, transpose the image.
        """
        self.transpose = self.image_palette["Flip XY"].get()
        if display and self.image is not None:
            self.image = self.flip_image(self.image)
            self.process_image()

    def toggle_min_max_buttons(self, display: bool = False) -> None:
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

    def try_to_display_image(self, image: np.ndarray) -> None:
        """Try to display an image using a single worker and a 1-deep queue.

        This enqueues the most recent frame and drops older frames if the queue is full.
        Also, rate-limits enqueues to `self.max_fps` (default 20 Hz).
        """

        # Throttle to max_fps (0 disables throttle)
        now = time.perf_counter()
        if (
            self._min_frame_interval > 0.0
            and (now - self._last_enqueue_time) < self._min_frame_interval
        ):
            # If we are receiving frames faster than the max_fps, drop this frame.
            return
        self._last_enqueue_time = now

        try:
            # Try to put the new frame into the queue.
            self._disp_q.put_nowait(image)

        except queue.Full:
            # If the queue is already full, we replace the oldest frame with the new
            # one.
            try:
                # Attempt to remove the oldest frame if it exists
                _ = self._disp_q.get_nowait()

                # Confirm that we successfully removed the oldest frame
                self._disp_q.task_done()
            except queue.Empty:
                pass

            try:
                # Now put the new frame into the queue
                self._disp_q.put_nowait(image)

            except queue.Full:
                # Just in case...
                pass

    def _display_worker(self) -> None:
        """Background worker that serially processes display requests."""
        while True:
            image = self._disp_q.get()
            try:
                self.display_image(image)
            except Exception as e:
                logger.exception("Error in display worker: %s", e)
            finally:
                self._disp_q.task_done()

    def display_image(self, image: np.ndarray) -> None:
        """Display an image.

        Parameters
        ----------
        image : np.ndarray
            Image data.
        """
        pass

    @staticmethod
    def _generate_lut(cmap_name: str) -> np.ndarray:
        """Create an OpenCV-compatible color lookup table.

        Parameters
        ----------
        cmap_name : str
            Name of the Matplotlib colormap.

        Returns
        -------
        numpy.ndarray
            Lookup table.
        """
        cmap = plt.get_cmap(cmap_name)
        return (cmap(np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)

    def apply_lut(self, image: np.ndarray) -> np.ndarray:
        """Apply a LUT to an 8-bit single-channel image.

        Parameters
        ----------
        image : np.ndarray
            8-bit image data (uint8), scaled to [0..255].

        Returns
        -------
        image : np.ndarray
            RGB image data with LUT applied.
        """
        image = np.require(image, dtype=np.uint8, requirements=["C"])
        lut = self.colormap
        h, w = image.shape[:2]
        if self._lut_buf is None or self._lut_buf.shape[:2] != (h, w):
            self._lut_buf = np.empty((h, w, 3), dtype=np.uint8)

        flat_idx = image.ravel()
        out = self._lut_buf.reshape(-1, 3)
        np.take(lut, flat_idx, axis=0, out=out)
        return self._lut_buf

    def identify_channel_index_and_slice(self) -> tuple:
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
            slice_idx = self.image_count % self.number_of_slices

        self.image_count += 1
        return channel_idx, slice_idx

    def initialize_non_live_display(
        self, microscope_state: dict, camera_parameters: dict
    ) -> None:
        """Initialize the non-live display.

        Parameters
        ----------
        microscope_state : dict
            Microscope state.
        camera_parameters : dict
            Camera parameters.
        """
        self.image_count = 0  # was image_counter
        self.slice_index = 0
        self.image_mode = microscope_state["image_mode"]
        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        self.get_selected_channels(microscope_state)
        self.number_of_channels = len(self.selected_channels)
        self.number_of_slices = int(microscope_state["number_z_steps"])
        self.total_images_per_volume = self.number_of_channels * self.number_of_slices
        self.original_image_width = int(camera_parameters["img_x_pixels"])
        self.original_image_height = int(camera_parameters["img_y_pixels"])

        if self.microscope_name is None:
            self.flip_flags = (
                self.parent_controller.configuration_controller.camera_flip_flags
            )
        else:
            camera_config = self.parent_controller.configuration["configuration"][
                "microscopes"
            ][self.microscope_name]["camera"]
            self.flip_flags = {
                "x": camera_config.get("flip_x", False),
                "y": camera_config.get("flip_y", False),
            }

        self.update_canvas_size()
        self.reset_display(False, False)

    def get_selected_channels(self, microscope_state: Optional[dict] = None) -> None:
        """Get the selected microscope channels from the MicroscopeState.

        Parameters
        ----------
        microscope_state : Optional[dict]
            The microscope state dictionary object.
        """
        if microscope_state is None:
            microscope_state = self.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]

        self.selected_channels = []
        for channel_name, channel_data in microscope_state["channels"].items():
            if channel_data["is_selected"]:
                channel_idx = channel_name.split("_")[-1]
                self.selected_channels.append(f"CH{channel_idx}")

    def reset_display(
        self, display_flag: bool = True, reset_crosshair: bool = True
    ) -> None:
        """Set the display back to the original digital zoom.

        Parameters
        ----------
        display_flag : bool
            Flag for refreshing the image display. Default True.
        reset_crosshair : bool
            Flag for resetting the crosshair. Default True.
        """
        if reset_crosshair:
            self.offset_crosshair = False
            self.crosshair_x = 0.5
            self.crosshair_y = 0.5
        self.zoom_width = self.canvas_width
        self.zoom_height = self.canvas_height
        self.zoom_rect = np.array([[0, self.zoom_width], [0, self.zoom_height]])
        self.zoom_offset = np.array([[0], [0]])
        self.zoom_value = 1
        self.zoom_scale = 1
        if display_flag:
            self.process_image()

    def move_crosshair(self) -> None:
        """Move the crosshair to a non-default position."""
        self.offset_crosshair = True
        width = (self.zoom_rect[0][1] - self.zoom_rect[0][0]) / self.zoom_scale
        height = (self.zoom_rect[1][1] - self.zoom_rect[1][0]) / self.zoom_scale
        self.crosshair_x = self.move_to_x / width
        self.crosshair_y = self.move_to_y / height
        self.process_image()

    def mark_position(self) -> None:
        """Marks the current position of the microscope in
        the multi-position acquisition table."""

        self.parent_controller.execute("query_stages")

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

            # get the pixel offsets
            stage_position["x_pixel"] = (
                self.move_to_x / self.zoom_scale * self.canvas_width_scale
            )
            stage_position["y_pixel"] = (
                self.move_to_y / self.zoom_scale * self.canvas_height_scale
            )

            # Place the stage position in the multi-position table.
            self.parent_controller.execute("mark_position", stage_position)

    def popup_menu(self, event: tk.Event) -> None:
        """Right-Click Popup Menu

        Parameters
        ----------
        event : tk.Event
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

    def calculate_offset(self) -> tuple:
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

    def move_stage(self) -> None:
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
            messagebox.showerror(
                title="Warning", message="Can't move to there! Invalid stage position!"
            )

    def update_canvas_size(self) -> None:
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

    def digital_zoom(self) -> np.ndarray:
        """Apply digital zoom.

        The x and y positions are between 0 and the canvas width and height
        respectively.

        Returns
        -------
        image : np.ndarray
            Image after digital zoom applied
        """
        self.zoom_rect = self.zoom_rect - self.zoom_offset
        self.zoom_rect = self.zoom_rect * self.zoom_value
        self.zoom_rect = self.zoom_rect + self.zoom_offset
        self.zoom_offset.fill(0)
        self.zoom_value = 1

        if self.zoom_rect[0][0] > 0 or self.zoom_rect[1][0] > 0:
            self.reset_display(False, False)

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

    def down_sample_image(self, image: np.ndarray) -> np.ndarray:
        """Down-sample the data for image display according to widget size.

        Interpolation type is cv2.INTER_LINEAR by default.

        Parameters
        ----------
        image : np.ndarray
            Image data.

        Returns
        -------
        down_sampled_image : np.ndarray
            Down-sampled image data.
        """
        sx, sy = self.canvas_width, self.canvas_height
        down_sampled_image = cv2.resize(
            src=image, dsize=(sx, sy), interpolation=cv2.INTER_NEAREST
        )
        return down_sampled_image

    def scale_image_intensity(self, image: np.ndarray) -> np.ndarray:
        """Scale the data to the min/max counts, and adjust bit-depth.

        Notes
        -----
        For autoscaled image intensity, with numpy, it was taking around 6ms. With
        cv2, this is reduced to 300 microseconds. With non autoscaled data,
        still taking around 4 ms. Need to change the trace.

        Parameters
        ----------
        image : np.ndarray
            Image data.

        Returns
        -------
        image : np.ndarray
            Scaled image data (uint8).
        """
        # Compute min/max once and reuse; also store display max
        min_value, max_value, _, _ = cv2.minMaxLoc(image)
        self._last_frame_display_max = max_value

        if self.autoscale:
            # In the off chance that we get a flat image, we set the min and max.
            if max_value > min_value:
                scale = 255.0 / (max_value - min_value)
                beta = -min_value * scale
                return cv2.convertScaleAbs(image, alpha=scale, beta=beta)

        # If autoscale is disabled, we use the min/max counts from the GUI.
        if self.max_counts > self.min_counts:
            scale = 255.0 / (self.max_counts - self.min_counts)
            beta = -self.min_counts * scale
            return cv2.convertScaleAbs(image, alpha=scale, beta=beta)

        # If the user has provided incorrect min/max values, we return a flat image.
        return np.ones_like(image, dtype=np.uint8) * 255

    def add_crosshair(self, image: np.ndarray) -> np.ndarray:
        """Adds a cross-hair to the image.

        Parameters
        ----------
        image : np.ndarray
            Image data.

        Returns
        -------
        image : np.ndarray
            Image data with cross-hair.
        """
        if self.apply_cross_hair:
            if self.offset_crosshair:
                width = (self.zoom_rect[0][1] - self.zoom_rect[0][0]) / self.zoom_scale
                height = (self.zoom_rect[1][1] - self.zoom_rect[1][0]) / self.zoom_scale
                crosshair_x = self.crosshair_x * width
                crosshair_y = self.crosshair_y * height
            else:
                crosshair_x = (
                    self.zoom_rect[0][1] - self.zoom_rect[0][0]
                ) * self.crosshair_x + self.zoom_rect[0][0]
                crosshair_y = (
                    self.zoom_rect[1][1] - self.zoom_rect[1][0]
                ) * self.crosshair_y + self.zoom_rect[1][0]

            if crosshair_x < 0 or crosshair_x >= self.canvas_width:
                crosshair_x = -1
            if crosshair_y < 0 or crosshair_y >= self.canvas_height:
                crosshair_y = -1
            image[:, int(crosshair_x)] = 255
            image[int(crosshair_y), :] = 255

        return image

    def get_absolute_position(self) -> tuple:
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

    def _ensure_canvas_image(self, w: int, h: int, mode: str) -> None:
        """Create/recreate the backing PhotoImage when size or mode changes.

        This is used to ensure that the canvas image is always the correct size and
        mode, but we do not have to create a new PhotoImage object every time we
        update the image. We incur a 1x ~14 ms cost for creating the initial object.
        Thereafter, the operation is essentially free.

        Parameters
        ----------
        w : int
            Width of the image.
        h : int
            Height of the image.
        mode : str
            Mode of the image (e.g., "RGB", "L", "RGBA").
        """
        need_new = (
            getattr(self, "_photo", None) is None
            or self._photo.width() != w
            or self._photo.height() != h
            or getattr(self, "_photo_mode", None) != mode
        )
        if need_new:
            # create a base PIL image
            base = Image.new(mode, (w, h))
            self._photo = ImageTk.PhotoImage(base)
            self._photo_mode = mode

            if getattr(self, "_img_item", None) is None:
                self._img_item = self.canvas.create_image(
                    0, 0, image=self._photo, anchor="nw"
                )
            else:
                # Reuse the same canvas item, just rebind the image
                self.canvas.itemconfig(self._img_item, image=self._photo)

    def populate_image(self, image: np.ndarray) -> None:
        """Update the Tk canvas using a persistent PhotoImage + paste.

        This is a zero-copy operation that allows us to update the canvas image
        without creating a new PhotoImage object every time. This is much faster than
        creating a new PhotoImage object and reconfiguring the canvas item. Copying
        the image from a buffer is between 100 and 800 microseconds. Pasting the
        image is between 3 and 5 ms.

        Parameters
        ----------
        image : np.ndarray
            The image data to be displayed on the canvas.

        """

        try:
            h, w = image.shape[:2]

            # infer mode from number of dimensions.
            if image.ndim == 2:
                mode = "L"
            elif image.shape[2] == 3:
                mode = "RGB"
            elif image.shape[2] == 4:
                mode = "RGBA"
            else:
                raise ValueError(f"Unsupported image shape {image.shape}")

            self._ensure_canvas_image(w, h, mode)

            # zero-copy wrap of the numpy buffer into a PIL image
            # keep a reference so the buffer stays alive while Tk reads it
            self._img_buf = image
            pil = Image.frombuffer(mode, (w, h), image, "raw", mode, 0, 1)

            # fast in-place update; no new PhotoImage objects, no new canvas items
            self._photo.paste(pil)

        except tk.TclError:
            return

    def render(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Process the image to be displayed.

        Parameters
        ----------
        image : np.ndarray
            Image data to be processed.

        Returns
        -------
        image : np.ndarray

        Applies digital zoom, down-samples the image, scales the
        image intensity, adds a crosshair, applies the lookup table, and populates the
        image.
        """
        if image is None:
            return None

        # Digital zoom takes ~0.0000 seconds
        image = self.digital_zoom()

        # Down-sampling zoom takes ~0.0002 seconds
        image = self.down_sample_image(image)

        # Transposing zoom takes ~0.0000 seconds
        image = self.transpose_image(image)

        # Scaling intensity zoom takes ~0.0002 seconds
        image = self.scale_image_intensity(image)

        # Adding crosshair zoom takes ~0.0000 seconds
        image = self.add_crosshair(image)

        # Applying LUT zoom takes ~0.0048 seconds
        image = self.apply_lut(image)

        return image

    def process_image(self) -> None:
        """Processes the image to be displayed."""
        if self.image is None:
            return

        # Populating image took 0.0158 seconds
        image = self.render(self.image)
        self.populate_image(image)

    def left_click(self, *_) -> None:
        """Toggles cross-hair on image upon left click event."""
        if self.image is not None:
            self.apply_cross_hair = not self.apply_cross_hair
            self.process_image()

    def resize(self, event: tk.Event) -> None:
        """Resize the window.

        Parameters
        ----------
        event : tk.Event
            Tkinter event.
        """
        if not self.parent_controller.resize_ready_flag:
            return
        if event.width < 512 or event.height < 512:
            return
        if event.widget != self.view:
            return
        if self.view.is_docked:
            left_width = self.parent_controller.view.left_frame.winfo_width()
            top_height = self.parent_controller.view.top_frame.winfo_height()
            w_width = self.parent_controller.view.winfo_width()
            w_height = self.parent_controller.view.winfo_height()
            width = max(w_width - left_width - 16, 560 + self.view.lut.winfo_width())
            height = max(w_height - top_height - 50, 670)
        else:
            width = event.width
            height = event.height - 24

        if self.resize_event_id:
            self.view.after_cancel(self.resize_event_id)
        self.resize_event_id = self.view.after(300, lambda: self.refresh(width, height))

    def refresh(self, width: int, height: int) -> None:
        """Refresh the window.

        Parameters
        ----------
        width : int
            Width of the window.
        height : int
            Height of the window.
        """
        if (
            self.width
            and self.height
            and abs(width - self.width) < 10
            and abs(height - self.height) < 10
        ):
            return
        self.canvas_width = width - self.view.lut.winfo_width() - 24
        widget_height = 0
        for widget in self.view.cam_image.winfo_children():
            if widget != self.view.canvas:
                if self.view.is_docked or widget.winfo_ismapped():
                    widget_height += widget.winfo_height() + 5
                    if widget.winfo_height() < 30:
                        widget_height += 30

        self.canvas_height = (
            height - widget_height - (50 if self.view.is_docked else -5)
        )
        self.view.canvas.config(width=self.canvas_width, height=self.canvas_height)
        self.view.update_idletasks()

        self.width, self.height = width, height

        # if resize the window during acquisition, the image showing should be updated
        self.update_canvas_size()
        self.reset_display(False)

    def update_min_max_counts(self, display: bool = False):
        """Get min and max count values from the View.

        When the min and max counts are toggled in the GUI, this function is called.
        Updates the min and max values.

        Parameters
        ----------
        display : bool
            Flag to display the image.
        """
        if self.image_palette["Min"].get() != "":
            self.min_counts = float(self.image_palette["Min"].get())
        if self.image_palette["Max"].get() != "":
            self.max_counts = float(self.image_palette["Max"].get())
        if display and self.image is not None:
            self.process_image()
        logger.info(
            f"Min and Max counts scaled to, {self.min_counts}, {self.max_counts}"
        )

    def mouse_wheel(self, event: tk.Event) -> None:
        """Digitally zooms in or out on the image upon scroll wheel event.

        Sets the self.zoom_value between 0.05 and 1 in .05 unit steps.

        Parameters
        ----------
        event : tk.Event
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
            self.reset_display(display_flag=False, reset_crosshair=False)
        elif self.zoom_width < 5 or self.zoom_height < 5:
            return

        self.process_image()


class CameraViewController(BaseViewController):
    """Camera View Controller Class."""

    def __init__(self, view, parent_controller=None) -> None:
        """Initialize the Camera View Controller Class.

        Parameters
        ----------
        view : CameraTab
            The Camera tkinter frame that contains the widgets.
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

        self.resize_event_id = self.view.bind("<Configure>", self.resize)

        #: str: The display state.
        self.display_state = "Live"

        #: int: The number of frames to average.
        self.rolling_frames = 1

        #: list: The list of maximum intensity values.
        self.max_intensity_history = [0] * 32

        #: int: The index of the latest maximun intesity value in the list.
        self._max_intensity_history_idx = 0

        #: bool: The flag for displaying the mask.
        self.display_mask_flag = False

        #: bool: The display mask flag.
        self.mask_color_table = None

        #: threading.Lock: The lock for the ilastik mask.
        self.ilastik_mask_ready_lock = threading.Lock()

        #: numpy.ndarray: The ilastik mask.
        self.ilastik_seg_mask = None

    def render(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Process the image to be displayed.

        Parameters
        ----------
        image : np.ndarray
            Image data to be processed.

        Returns
        -------
        image : np.ndarray

        Applies digital zoom, down-samples the image, scales the
        image intensity, adds a crosshair, applies the lookup table, and populates the
        image.
        """
        if image is None:
            return None

        image = super().render(image)

        # Overlaying mask
        image = self.overlay_mask(image)

        return image

    def overlay_mask(self, image: np.ndarray, alpha=0.2) -> Optional[np.ndarray]:
        """Overlay a mask on top of the image

        Parameters
        ----------
        image : np.ndarray
            Image data to be processed.
        alpha : float
            The mask blending ratio.

        Returns
        -------
        image : np.ndarray

        Overlays a mask if avaiable.
        """
        if image is None:
            return None
        if self.display_mask_flag and self.display_state == "Live":
            self.ilastik_mask_ready_lock.acquire()
            seg_mask = cv2.resize(self.ilastik_seg_mask, image.shape[:2])
            if alpha > 1:
                alpha = 1
            if alpha < 0:
                alpha = 0
            image = cv2.addWeighted(image, 1 - alpha, seg_mask, alpha, 0)
        return image

    def try_to_display_image(self, image: np.ndarray) -> None:
        """Try to display an image.

        In the live mode, images are automatically passed to the display function.

        In the slice mode, images are passed to a spooled temporary file. However,
        when the same slice and channel index is acquired again, the image is
        updated. In all other cases, the image is only displayed upon slider events.

        Parameters
        ----------
        image : np.ndarray
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

    def initialize_non_live_display(
        self, microscope_state: dict, camera_parameters: dict
    ) -> None:
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
        self.view.live_frame.channel.set(self.selected_channels[0])
        self.spooled_images = SpooledImageLoader(
            channels=self.number_of_channels,
            size_y=self.original_image_height,
            size_x=self.original_image_width,
        )

    def update_snr(self) -> None:
        """Updates the signal-to-noise ratio."""
        off, var = self.parent_controller.model.get_offset_variance_maps()
        if off is None:
            self.image_palette["SNR"].grid_remove()
        else:
            self._offset, self._variance = copy.deepcopy(off), copy.deepcopy(var)
            self.image_palette["SNR"].grid(row=3, column=0, sticky=tk.W,
                                           pady=3)

    def slider_update(self, *_) -> None:
        """Updates the image when the slider is moved."""

        slider_index = self.view.slider.get()
        channel_index = self.view.live_frame.channel.get()
        channel_index = self.selected_channels.index(channel_index)
        image = self.spooled_images.load_image(
            channel=channel_index, slice_index=slider_index
        )

        if image is None:
            return

        self.image = self.flip_image(image)
        self.process_image()
        self.update_max_counts()

    def update_display_state(self, *_) -> None:
        """Image Display Combobox Called.

        Sets self.display_state to desired display format. Toggles state of slider
        widget. Sets number of positions.
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
            self.view.live_frame.channel.state(["!disabled", "readonly"])
            # was normal
            if self.view.live_frame.channel.get() not in self.selected_channels:
                self.view.live_frame.channel.set(self.selected_channels[0])

    def initialize(self, name: str, data: list):
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

    def set_mode(self, mode: str = ""):
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

    def update_max_counts(self) -> None:
        """Update the max counts in the camera view.

        Function gets the number of frames to average from the VIEW.

        If frames to average == 0 or 1, provides the maximum value from the last
        acquired data.
        """
        # record the max without rescanning the full frame
        self.max_intensity_history[self._max_intensity_history_idx] = (
            self._last_frame_display_max
        )
        self._max_intensity_history_idx = (self._max_intensity_history_idx + 1) % 32

        # Get the number of frames to average from the VIEW
        self.rolling_frames = int(self.image_metrics["Frames"].get())

        if self.rolling_frames <= 0:
            # Cannot average 0 frames. Set to 1, and report max intensity
            self.rolling_frames = 1
            self.image_metrics["Frames"].set(1)
            rolling_average = self._last_frame_display_max
        elif self.rolling_frames == 1:
            rolling_average = self._last_frame_display_max
        elif self._max_intensity_history_idx >= self.rolling_frames:

            rolling_average = (
                sum(
                    self.max_intensity_history[
                        self._max_intensity_history_idx
                        - self.rolling_frames : self._max_intensity_history_idx
                    ]
                )
                / self.rolling_frames
            )
        else:
            temp = sum(
                self.max_intensity_history[
                    self._max_intensity_history_idx - self.rolling_frames :
                ]
            ) + sum(self.max_intensity_history[0 : self._max_intensity_history_idx])
            rolling_average = temp / self.rolling_frames

        self.image_metrics["Image"].set(f"{rolling_average:.0f}")

    @performance_monitor(prefix="Image Display", display_result=lambda x: {"image_id": int(x)})
    def display_image(self, image: np.ndarray) -> None:
        """Display an image using the LUT specified in the View.

        If Autoscale is selected, automatically calculates the min and max values for the data.

        If Autoscale is not selected, takes the user values as specified in the min
        and max counts.

        Parameters
        ----------
        image : np.ndarray
            Image data.
        """

        self.image = self.flip_image(image)

        if self._snr_selected:
            self.image = compute_signal_to_noise(
                self.image, self._offset, self._variance
            )

        img_out = self.render(self.image)

        # Schedule the image to be displayed in the Tkinter main loop
        self.view.after(0, lambda img=img_out: self.populate_image(img))

        self.update_max_counts()

        return self.image_count

    def set_mask_color_table(self, colors: list) -> None:
        """Set up segmentation mask color table

        Parameters
        ----------
        colors : list
            The list of colors to use for the segmentation mask
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

    def display_mask(self, mask: np.ndarray) -> None:
        """Display segmentation mask

        Parameters
        ----------
        mask : np.ndarray
            Segmentation mask to display
        """
        self.ilastik_seg_mask = cv2.applyColorMap(mask, self.mask_color_table)
        self.ilastik_mask_ready_lock.release()

    @property
    def custom_events(self):
        """dict: Custom events for this controller"""
        return {"ilastik_mask": self.display_mask}


class MIPViewController(BaseViewController):
    """MIP View Controller Class."""

    def __init__(self, view, parent_controller=None) -> None:
        """Initialize the MIP View Controller Class.

        Parameters
        ----------
        view : MIPTab
            The MIP tkinter frame that contains the widgets.
        parent_controller : Controller
            The parent controller of the camera view controller.
        """
        super().__init__(view, parent_controller)

        #: tkinter.Canvas: The tkinter canvas that displays the image.
        self.view = view

        #: int: The image height.
        self.XY_image_height = None

        #: int: The image width.
        self.XY_image_width = None

        #: int: Scaling factor for ratio of lateral and axial dimensions.
        self.Z_image_value = None

        #: np.ndarray: The image data.
        self.image = None

        #: np.ndarray: The maximum intensity projection in the ZY plane.
        self.zx_mip = None

        #: np.ndarray: The maximum intensity projection in the ZY plane.
        self.zy_mip = None

        #: np.ndarray: The maximum intensity projection in the XY plane.
        self.xy_mip = None

        #: bool: The autoscale flag.
        self.autoscale = True

        #: str: The perspective of the image.
        self.perspective = "XY"

        #: dict: The render widgets.
        self.render_widgets = self.view.render.get_widgets()

        self.resize_event_id = self.view.bind("<Configure>", self.resize)

        #: bool: The display enabled flag.
        self.display_enabled = tk.BooleanVar()

        self.menu.entryconfig("Move Here", state="disabled")
        self.menu.entryconfig("Mark Position", state="disabled")
        self.menu.add_separator()
        self.menu.add_checkbutton(
            label="Enable MIP Display",
            variable=self.display_enabled,
            onvalue=True,
            offvalue=False,
            command=self.update_experiment,
        )

        # Default location for communicating with the plugin in the model.
        if "mip_display" not in self.parent_controller.configuration["gui"].keys():
            update_config_dict(
                manager=self.parent_controller.manager,
                parent_dict=self.parent_controller.configuration["gui"],
                config_name="mip_display",
                new_config={"enabled": True},
            )

        # Set histogram according to the experiment.yaml file. If disabled, stays disabled upon restart.
        self.display_enabled.set(
            self.parent_controller.configuration["gui"]["mip_display"].get(
                "enabled", True
            )
        )

    def update_experiment(self) -> None:
        """Update the experiment.yaml file"""
        state = self.display_enabled.get()
        self.parent_controller.configuration["gui"]["mip_display"]["enabled"] = state
        # Communicate changes back to the menu controller.
        self.parent_controller.menu_controller.mip_enabled.set(state)

    def initialize(self, name: str, data: list) -> None:
        """Initialize the MIP view.

        Sets the min and max intensity values for the image.Disables the min and max
        widgets. Invokes the gray and autoscale widgets.Hides the SNR widget.
        Sets the perspective widget values. Sets the perspective widget to XY. Sets
        the channel widget to CH0.

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

        self.get_selected_channels()
        if isinstance(self.selected_channels, list) and len(self.selected_channels) > 0:
            self.render_widgets["channel"].set(self.selected_channels[0])

        # event binding
        self.render_widgets["perspective"].get_variable().trace_add(
            "write", self.display_mip_image
        )
        self.render_widgets["channel"].get_variable().trace_add(
            "write", self.display_mip_image
        )

    def prepare_mip_view(self) -> None:
        """Prepare the MIP view.

        Set the number of channels, number of slices, and the selected channels.
        Pre-allocate the matrices for the MIP.
        """
        self.render_widgets["channel"].widget["values"] = self.selected_channels
        self.preallocate_matrices()

    def preallocate_matrices(self) -> None:
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

    def get_mip_image(self) -> np.ndarray or None:
        """Get MIP image according to perspective and channel id

        Returns
        -------
        image : np.ndarray or None
            Image data
        """
        views = [self.xy_mip, self.zy_mip, self.zx_mip]
        if any(view is None for view in views):
            return None

        display_mode = self.render_widgets["perspective"].get()
        channel = self.render_widgets["channel"].get()
        if channel in self.selected_channels:
            channel_idx = self.selected_channels.index(channel)
        else:
            return

        if display_mode == "XY":
            image = self.xy_mip[channel_idx]
        elif display_mode == "ZY":
            image = self.zy_mip[channel_idx, :].T
        else:
            image = self.zx_mip[channel_idx, :]

        image = self.flip_image(image)
        # map the image to canvas size()
        image = self.down_sample_image(image, True)
        return image

    def initialize_non_live_display(
        self, microscope_state: dict, camera_parameters: dict
    ) -> None:
        """Initialize the non-live display.

        Parameters
        ----------
        microscope_state : dict
            Microscope state.
        camera_parameters : dict
            Camera parameters.
        """
        super().initialize_non_live_display(microscope_state, camera_parameters)
        if isinstance(self.selected_channels, list) and len(self.selected_channels) > 0:
            self.render_widgets["channel"].set(self.selected_channels[0])
        self.perspective = self.render_widgets["perspective"].get()
        self.XY_image_width = self.original_image_width
        self.XY_image_height = self.original_image_height
        z_range = microscope_state["abs_z_end"] - microscope_state["abs_z_start"]

        # TODO: may stretch by the value of binning.
        if z_range == 0:
            self.Z_image_value = 1
        else:
            self.Z_image_value = int(
                self.XY_image_width * camera_parameters["fov_x"] / z_range
            )
        self.prepare_mip_view()
        self.update_perspective()

    def try_to_display_image(self, image: np.ndarray) -> None:
        """Display the image.

        Parameters
        ----------
        image : np.ndarray
            Image data.
        """
        channel_idx, slice_idx = self.identify_channel_index_and_slice()

        if self.image_mode in ["live", "single"]:
            return

        if not self.display_enabled.get():
            self._clear_mip()
            return

        # Orthogonal maximum intensity projections.
        self.xy_mip[channel_idx] = np.maximum(self.xy_mip[channel_idx], image)
        self.zy_mip[channel_idx, slice_idx] = np.maximum(
            self.zy_mip[channel_idx, slice_idx], np.max(image, axis=0)
        )
        self.zx_mip[channel_idx, slice_idx] = np.maximum(
            self.zx_mip[channel_idx, slice_idx], np.max(image, axis=1)
        )

        super().try_to_display_image(image)

    def _clear_mip(self) -> None:
        """Clear the mip but keep canvas interactive."""
        self.canvas.delete("all")
        self.tk_image = None
        self.canvas.create_text(
            self.canvas_width // 2,
            self.canvas_height // 2,
            text="Maximum Intensity Projection Disabled\nRight Click to Enable",
            font=("Arial", 14, "italic"),
            fill="gray",
            anchor="center",
            justify="center",
        )

    def display_image(self, image: np.ndarray) -> None:
        """Display an image using the LUT specified in the View.

        If Autoscale is selected, automatically calculates
        the min and max values for the data.

        If Autoscale is not selected, takes the user values
        as specified in the min and max counts.

        Parameters
        ----------
        image : np.ndarray
            Image data.
        """
        self.image = self.get_mip_image()
        self.process_image()

    def display_mip_image(self, *_) -> None:
        """Display MIP image in non-live view."""

        if self.perspective != self.render_widgets["perspective"].get():
            self.update_perspective()
        if self.mode != "stop":
            return
        self.image = self.get_mip_image()
        if self.image is not None:
            self.process_image()

    def update_perspective(self) -> None:
        """Update the perspective of the image."""
        attribute_list = [
            "XY_image_width",
            "XY_image_height",
            "Z_image_value",
        ]
        if any(
            not hasattr(self, attr) or getattr(self, attr) is None
            for attr in attribute_list
        ):
            return

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

    def down_sample_image(
        self, image: np.ndarray, reset_original: bool = False
    ) -> np.ndarray:
        """Down-sample the data for image display according to widget size.

        Parameters
        ----------
        image : np.ndarray
            Image data.
        reset_original : bool
            Flag to reset the original image size.

        Returns
        -------
        down_sampled_image : np.ndarray
            Down-sampled image data.
        """
        sx, sy = self.canvas_width, self.canvas_height
        down_sampled_image = cv2.resize(image, (sx, sy))
        if reset_original:
            self.original_image_width = self.canvas_width
            self.original_image_height = self.canvas_height
            self.canvas_width_scale = 1
            self.canvas_height_scale = 1
        return down_sampled_image


class SpooledImageLoader:
    """A class to lazily load images from disk using a spooled temporary file."""

    def __init__(self, channels: int, size_y: int, size_x: int) -> None:
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

    def __del__(self) -> None:
        """Delete the temporary files."""
        if self.temp_files is not None:
            for temp_file in self.temp_files.values():
                temp_file.close()

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

    def save_image(self, image: np.ndarray, channel: int, slice_index: int) -> None:
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

    def load_image(self, channel: int, slice_index: int) -> np.ndarray or None:
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

    def get_indices(self, slice_index: int) -> tuple:
        """Get the indices of the images stored in the spooled files.

        Parameters
        ----------
        slice_index : int
            The slice index.

        Returns
        -------
        tuple[int, int]
            The start and end indices of the images.
        """

        start_idx = slice_index * self.n_bytes
        end_idx = start_idx + self.n_bytes
        return start_idx, end_idx
