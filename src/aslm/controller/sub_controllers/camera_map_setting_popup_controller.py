import os
from pathlib import Path

import numpy as np
import tifffile
from tkinter import filedialog

from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.config import get_aslm_path
from aslm.model.analysis.camera import compute_scmos_offset_and_variance_map


class CameraMapSettingPopupController(GUIController):
    def __init__(self, view, parent_controller=None):
        """
        Popup used to generate offset and variance maps of a camera from a
        series of dark frames. The maps are useful for estimating signal-
        to-noise ratios.
        """
        super().__init__(view, parent_controller)

        self.map_path = os.path.join(get_aslm_path(), "camera_maps")
        self.off = None
        self.var = None

        self.view.open_btn.configure(command=self.open_frames)
        self.view.map_btn.configure(command=self.create_camera_maps)

        menu = self.get_camera_menu()
        self.view.inputs["camera"].set_menu(menu[0], *menu)

    def showup(self):
        self.view.showup()

    def get_camera_menu(self):
        """Return list of serial numbers of available cameras."""
        menu = ["synthetic"]
        for v in self.parent_controller.configuration["configuration"][
            "microscopes"
        ].values():
            menu.append(v["camera"]["hardware"]["serial_number"])
        return menu

    def open_frames(self):
        filename = filedialog.askopenfilename(
            defaultextension=".tif", filetypes=[("tiff files", "*.tif *.tiff")]
        )
        if not filename:
            return
        self.view.file_name.set(filename)

    def create_camera_maps(self):
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
