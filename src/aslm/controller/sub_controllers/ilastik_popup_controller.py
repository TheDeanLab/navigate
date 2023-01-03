# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

from tkinter import filedialog, messagebox, Checkbutton, Label
import traceback

from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.model.features.restful_features import prepare_service

import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class IlastikPopupController(GUIController):
    def __init__(self, view, parent_controller, service_url):
        super().__init__(view, parent_controller)

        self.service_url = service_url
        self.project_filename = None
        self.show_segmentation_flag = False
        self.mark_position_flag = False
        self.label_dict = None
        self.showup()

    def load_project(self):
        filename = filedialog.askopenfilename(
            defaultextension=".ilp", filetypes=[("Ilastik Project File", "*.ilp")]
        )
        try:
            r = prepare_service(self.service_url, project_file=filename)
            message = "There is something wrong when loading the ilastik project file, please make sure the file exists and is correct!"
        except Exception as e:
            r = None
            message = "Please make sure the aslm_server for ilastik is running!"
            logger.debug(e)
            logger.debug(traceback.format_exc())

        # destroy current labels
        for child in self.label_frame.winfo_children():
            child.destroy()

        if not r:
            self.project_filename = None
            self.project_filename_var.set(
                "Please select an ilastik pixelclassification project file!"
            )
            messagebox.showerror(title="Ilastik Error", message=message)
        else:
            self.project_filename = filename
            r["status"] = [False] * len(r["names"])
            self.label_dict = r
            self.update_project(filename, r)

    def update_project(self, filename, label_dict):
        self.project_filename_var.set(filename)
        logger.info(f"{filename} is loaded successfully!")

        # redraw new labels
        for i, label_name in enumerate(label_dict["names"]):
            label_widget = Checkbutton(
                self.label_frame, text=label_name, command=self.toggle_label(i)
            )
            label_widget.grid(
                row=1 + i, column=0, pady=(0, 10), padx=(20, 5), sticky="W"
            )
            if label_dict["status"][i]:
                label_widget.select()
            color_block = Label(
                self.label_frame,
                background=label_dict["label_colors"][i],
                width=3,
                height=1,
            )
            color_block.grid(row=1 + i, column=1, pady=(0, 10), padx=(0, 10))

    def toggle_label(self, label_id):
        def func():
            self.label_dict["status"][label_id] = not self.label_dict["status"][
                label_id
            ]

        return func

    def toggle_display(self):
        self.show_segmentation_flag = not self.show_segmentation_flag

    def toggle_mark_position(self):
        self.mark_position_flag = not self.mark_position_flag

    def confirm_setting(self):
        """confirm setting

        tell the model which labels will be used
        activate features containing ilastik
        """
        # update ilastik menu status
        ilastik_menu_state = "normal" if self.project_filename else "disabled"
        self.parent_controller.view.menubar.menu_features.entryconfig(
            "Ilastik Segmentation", state=ilastik_menu_state
        )
        # update segmentation mask color map
        self.parent_controller.camera_view_controller.set_mask_color_table(
            self.label_dict["label_colors"]
        )
        # tell model the target label
        if (
            self.show_segmentation_flag == False
            and self.mark_position_flag == False
            or (self.mark_position_flag and True not in self.label_dict["status"])
        ):
            messagebox.showwarning(
                "Warning", message="You haven't select any usage or target label!"
            )
            self.parent_controller.view.menubar.menu_features.entryconfig(
                "Ilastik Segmentation", state="disabled"
            )
        else:
            self.parent_controller.model.update_ilastik_setting(
                **{
                    "display_segmentation": self.show_segmentation_flag,
                    "mark_position": self.mark_position_flag,
                    "target_labels": [
                        i + 1 for i, x in enumerate(self.label_dict["status"]) if x
                    ],
                }
            )
            # close the window
            self.view.popup.dismiss()

    def showup(self, popup_window=None):
        """show the popup window

        this function will let the popup window show in front
        """
        if popup_window is not None:
            self.view = popup_window
        self.view.popup.protocol("WM_DELETE_WINDOW", self.view.popup.dismiss)
        buttons = self.view.get_buttons()
        buttons["load"].configure(command=self.load_project)
        buttons["confirm"].configure(command=self.confirm_setting)

        self.project_filename_var = self.view.get_variables()["project_name"]
        widgets = self.view.get_widgets()
        self.label_frame = widgets["label_frame"]
        show_seg_widget = widgets["show_segmentation"]
        mark_pos_widget = widgets["mark_position"]

        # segmentation
        if self.show_segmentation_flag:
            show_seg_widget.select()
        if self.mark_position_flag:
            mark_pos_widget.select()

        show_seg_widget.configure(command=self.toggle_display)
        mark_pos_widget.configure(command=self.toggle_mark_position)

        if self.project_filename is not None:
            # destroy current labels
            for child in self.label_frame.winfo_children():
                child.destroy()
            self.update_project(self.project_filename, self.label_dict)
