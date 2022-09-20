"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
from aslm.controller.sub_controllers.gui_controller import GUI_Controller
from aslm.view.custom_widgets.validation import ValidatedEntry
import tkinter as tk
import logging
import platform

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class KeystrokeController(GUI_Controller):
    def __init__(self, main_view, parent_controller, configuration_controller=None):
        super().__init__(main_view, parent_controller)

        # References to all sub frames
        self.camera_view = main_view.camera_waveform.camera_tab # Camera View
        self.multi_table = main_view.settings.multiposition_tab.multipoint_list # Multiposition Table
        self.main_view = main_view.root # Main view
        self.main_tabs = main_view.settings

        # Controllers for all sub frames
        self.camera_controller = parent_controller.camera_view_controller
        self.multi_controller = parent_controller.multiposition_tab_controller
        self.stage_controller = parent_controller.stage_gui_controller

        """Keystrokes for Camera View"""
        # Left Click binding
        self.camera_view.canvas.bind("<Button-1>", self.camera_controller.left_click)

        # Slider Binding
        self.camera_view.slider.bind("<Button-1>", self.camera_controller.slider_update)

        # MouseWheel Binding
        self.view.root.bind("<MouseWheel>", self.view.scroll_frame.mouse_wheel)
        self.camera_view.canvas.bind("<Enter>", self.camera_controller_mouse_wheel_enter)
        self.camera_view.canvas.bind("<Leave>", self.camera_controller_mouse_wheel_leave)

        # Right Click Binding
        if platform.system() == 'Darwin':
            self.camera_view.canvas.bind("<Button-2>", self.camera_controller.popup_menu)
        else:
            self.camera_view.canvas.bind("<Button-3>", self.camera_controller.popup_menu)

        """Keystrokes for MultiTable"""
        self.mp_table = self.multi_table.pt
        self.mp_table.rowheader.bind("<Double-Button-1>", self.multi_controller.handle_double_click)

        """Keystrokes for Main Window"""
        self.main_view.bind("<Key>", self.stage_controller.key_press)
        # self.main_view.bind("<Key>", self.test)
        self.main_view.bind("1", self.switch_tab1)
        self.main_view.bind("2", self.switch_tab2)
        self.main_view.bind("3", self.switch_tab3)
        self.main_view.bind("4", self.switch_tab4)
        self.main_view.bind_all('z', self.undo)
        self.main_view.bind_all('y', self.redo) # May need to bind individually bind all may not be a good way to do it
        

    # def test(self, event):
    #     print(event.state)
    #     print(event.keysym)
    #     print(event.keycode)
    #     print(event)


    def camera_controller_mouse_wheel_enter(self, event):
        self.view.root.unbind("<MouseWheel>")  # get rid of scrollbar mousewheel
        if platform.system() != 'Linux':
            self.camera_view.canvas.bind("<MouseWheel>", self.camera_controller.mouse_wheel)
        else:
            self.camera_view.canvas.bind("<Button-4>", self.camera_controller.mouse_wheel)
            self.camera_view.canvas.bind("<Button-5>", self.camera_controller.mouse_wheel)

    def camera_controller_mouse_wheel_leave(self, event):
        if platform.system() != "Linux":
            self.camera_view.canvas.unbind("<MouseWheel>")
        else:
            self.camera_view.canvas.unbind("<Button-4>")
            self.camera_view.canvas.unbind("<Button-5>")
        self.view.root.bind("<MouseWheel>", self.view.scroll_frame.mouse_wheel)  # reinstate scrollbar mousewheel

    # Refactorable when we have time

    def switch_tab1(self, event):
        if event.state == 4:
            if self.main_tabs.index("end") > 0:
                self.main_tabs.select(0)

    def switch_tab2(self, event):
        if event.state == 4:
            if self.main_tabs.index("end") > 1:
                self.main_tabs.select(1)
    
    def switch_tab3(self, event):
        if event.state == 4:
            if self.main_tabs.index("end") > 2:
                self.main_tabs.select(2)

    def switch_tab4(self, event):
        if event.state == 4:
            if self.main_tabs.index("end") > 3:
                self.main_tabs.select(3)


    # Need to make sure that the entry is undo/redo and that the underlying variable for the entry is being updated to what is shown

    def undo(self, event):
        print("Undo process started")
        if isinstance(event.widget, ValidatedEntry): #Add all widgets that you want to be able to undo here
            widget = event.widget
            print("Entry being tested: ", widget)
            print("State of widget: ", widget.state)
            print("Undo history of widget: ", widget.undo_history)
            if event.state == 4:
                if len(widget.undo_history) > 1:
                    print("Undo really starting now")
                    widget.delete(0, tk.END)
                    print("Widget delete")
                    widget.insert(tk.END, widget.undo_history[-2]) # Should this be widget.variable.set()
                    print("Widget insert: ", widget.undo_history[-2])
                    widget.redo_history.append(widget.undo_history.pop())
                    print("Adding to redo history: ", widget.redo_history)
                if len(widget.undo_history) == 1:
                    widget.delete(0, tk.END)
                    print("Widget delete bc less than 1")
                    widget.redo_history.append(widget.undo_history.pop())


    def redo(self, event):
        print("Redo process started")
        if isinstance(event.widget, ValidatedEntry):
            widget = event.widget
            if event.state == 4:
                if widget.redo_history:
                    widget.delete(0, tk.END)
                    widget.insert(tk.END, widget.redo_history[-1])
                    widget.undo_history.append(widget.redo_history.pop())

        