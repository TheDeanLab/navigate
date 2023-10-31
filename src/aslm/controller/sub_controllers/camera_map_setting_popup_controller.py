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

# Standard library imports
import os
from pathlib import Path
from tkinter import filedialog

# Third party imports
import tifffile

# Local application imports
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.config import get_aslm_path
from aslm.model.analysis.camera import compute_scmos_offset_and_variance_map


class CameraMapSettingPopupController(GUIController):
    """Controller for the camera map setting popup."""

    def __init__(self, view, parent_controller=None):
        """Controller for the camera map setting popup.

        Popup used to generate offset and variance maps of a camera from a
        series of dark frames. The maps are useful for estimating signal-
        to-noise ratios.

        Parameters
        ----------
        view : aslm.view.sub_views.camera_map_setting_popup.CameraMapSettingPopup
            View for the camera map setting popup.
        parent_controller : aslm.controller.main_controller.MainController
            Parent controller of this controller.
        """
        super().__init__(view, parent_controller)
        #: str: Path to the camera maps directory.
        self.map_path = os.path.join(get_aslm_path(), "camera_maps")
        #: np.ndarray: Offset map.
        self.off = None
        #: np.ndarray: Variance map.
        self.var = None

        self.view.open_btn.configure(command=self.open_frames)
        self.view.map_btn.configure(command=self.create_camera_maps)

        menu = self.get_camera_menu()
        self.view.inputs["camera"].set_menu(menu[0], *menu)

    def showup(self):
        """Show the popup.

        This method is called by the parent controller.

        Example
        -------
        >>> self.parent_controller.show_popup("camera_map_setting_popup")
        """
        self.view.showup()

    def get_camera_menu(self):
        """Return list of serial numbers of available cameras.

        Returns
        -------
        menu : list
            Serial numbers of available cameras.
        """
        menu = ["synthetic"]
        for v in self.parent_controller.configuration["configuration"][
            "microscopes"
        ].values():
            menu.append(v["camera"]["hardware"]["serial_number"])
        return menu

    def open_frames(self):
        """Open a file dialog to select a series of dark frames."""
        filename = filedialog.askopenfilename(
            defaultextension=".tif", filetypes=[("tiff files", "*.tif *.tiff")]
        )
        if not filename:
            return
        self.view.file_name.set(filename)

    def create_camera_maps(self):
        """Create offset and variance maps from a series of dark frames."""
        # TODO: This should not be in the controller logic.
        image_name = self.view.file_name.get()
        im = tifffile.imread(image_name)
        self.off, self.var = compute_scmos_offset_and_variance_map(im)

        self.display_plot()

        save_dir = self.map_path
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        camera_name = self.view.camera.get()
        save_name_offset = f"{camera_name}_off.tiff"
        save_name_variance = f"{camera_name}_var.tiff"
        save_path_offset = Path(save_dir).joinpath(save_name_offset)
        save_path_variance = Path(save_dir).joinpath(save_name_variance)

        tifffile.imsave(save_path_offset, self.off)
        tifffile.imsave(save_path_variance, self.var)

    def display_plot(self):
        """Display the offset and variance maps."""
        for ax in self.view.axs:
            ax.clear()

        self.view.axs[0].hist(self.off.ravel(), bins=range(0, 2**8))
        self.view.axs[1].hist(self.var.ravel() * 0.47 * 0.47, bins=range(0, 2**8))

        self.view.axs[0].set_xlabel("Offset (counts)")
        self.view.axs[0].set_ylabel("Frequency")
        self.view.axs[0].set_yscale("log")
        self.view.axs[1].set_xlabel("Variance (counts$^2$)")
        self.view.axs[1].set_ylabel("Frequency")
        self.view.axs[1].set_yscale("log")
        self.view.fig.tight_layout()

        self.view.fig.canvas.draw_idle()
