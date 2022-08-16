"""
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
from tkinter import ttk
import tkinter as tk
import logging
from pathlib import Path

#from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class hover(object):
    '''
    Takes in a widget to which the hover is bound and text (optional)
    Description setting is not done on initialization, must use hover.setdescription()
    '''
    def __init__(self, widget=None, text=None, type="free"):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.text = text
        self.description=None
        self.type = type
        
        #define event handling for showing and hiding the hover
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)
        widget.bind('<ButtonPress>', self.hide)

    # Sets a description for the widget to appear when hovered over
    # If text=None, no description hover will be shown at all
    def setdescription(self, text):
        self.description=text
    
    # Event handlers
    def show(self, event):
        if self.type=="free" and (not self.description==None):
            self.type="description"
            self.showtip(self.description)
    def hide(self, event):
        if self.type=="description":
            self.hidetip()

    def update_type(self, newtype):
        self.type=newtype
    
    def get_type(self):
        return self.type
    
    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        
        x, y, cx, cy = self.widget.bbox("insert")
        if self.type.lower() == "description":
            background="#ffffe0"
            relief = tk.SOLID
            font=("tahoma", "8", "normal")
            x = x+self.widget.winfo_rootx() + self.widget.winfo_width()
            y = y+self.widget.winfo_rooty() + self.widget.winfo_height()
        elif self.type.lower() == "error":
            background="#ff5d66"
            relief=tk.RIDGE,
            font=("comic sans", "8", "normal")
            x = x+self.widget.winfo_rootx()
            y = y+self.widget.winfo_rooty() + self.widget.winfo_height()
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background=background, relief=relief, borderwidth=1,
                      font=font)
        label.pack(ipadx=1)

    def seterror(self, text):
        self.type="error"
        self.showtip(text)
        
    def hidetip(self):
        self.type="free"
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()