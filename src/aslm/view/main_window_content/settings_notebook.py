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
# Standard Imports
import tkinter as tk
from tkinter import ttk
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


# Import Sub-Frames
from aslm.view.main_window_content.camera_display.camera_settings.camera_settings_tab import camera_settings_tab
from aslm.view.main_window_content.channel_settings.channels_tab import channels_tab


class settings_notebook(ttk.Notebook):
    def __init__(self, frame_left, root, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(self, frame_left, *args, **kwargs)

        # Current tab (tab is a reserved word for notebook hence cur_tab)
        self.cur_tab = None
        self.root = root
        
        # Formatting
        tk.Grid.columnconfigure(self, 'all', weight=1)
        tk.Grid.rowconfigure(self, 'all', weight=1)

        #Putting notebook 1 into left frame
        self.grid(row=0,column=0)

        #Creating the Channels tab
        self.channels_tab = channels_tab(self)


        #Creating the Camera tab
        self.camera_settings_tab = camera_settings_tab(self)


        #Adding tabs to settings notebook
        self.add(self.channels_tab, text='Channels', sticky=tk.NSEW)
        self.add(self.camera_settings_tab, text='Camera Settings', sticky=tk.NSEW)


        # Popup setup
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Popout Tab", command=self.popout)

        # Binding for Popup menu
        self.bind("<ButtonPress-2>", self.find)

    def get_absolute_position(self):
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        return x, y

    def find(self, event):
        element = event.widget.identify(event.x, event.y)
        self.cur_tab = event.widget.index(event.widget.select())
        if "label" in element:
            try:
                x, y = self.get_absolute_position()
                self.menu.tk_popup(x, y)
            finally:
                self.menu.grab_release()
    
    def popout(self):
        # Get ref to correct tab to popout
        tab = self.select()
        tab_text = ""
        text = self.tab('current')['text']
        split = text.split("_")
        for word in split:
            if word != "!" or word != "tab":
                tab_text += word.capitalize()
                tab_text += " "
        self.root.wm_manage(tab)
        # tab.wm_title(tab_text)
        print("tried chanigng text and protocol")
        tk.Wm.wm_title(tab, tab_text)
        tk.Wm.protocol(tab, "WM_DELETE_WINDOW", lambda: self.dismiss(tab, tab_text))
        # popup.protocol("WM_DELETE_WINDOW", lambda: self.dismiss(tab, tab_text))
    
    def dismiss(self, tab, tab_text):
        self.root.wm_forget(tab)
        print("Dismissing")
        self.add(tab, tab_text, sticky=tk.NSEW)
        print("tried adding back tab")
        self.grab_release()
        self.destroy()

        
    




