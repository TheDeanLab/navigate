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
# Logger Setup
p = Path(__file__).resolve().parts[7]
logger = logging.getLogger(p)

class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)
    widget.bind('<ButtonPress>', leave)

if __name__ == '__main__':
    root = tk.Tk()
    frame = ttk.Frame(root)

    btn_ne = ttk.Button(frame, text='North East')
    btn_se = ttk.Button(frame, text='South East')
    btn_sw = ttk.Button(frame, text='South West')
    btn_nw = ttk.Button(frame, text='North West')
    btn_center = ttk.Button(frame, text='Center')
    btn_n = ttk.Button(frame, text='North')
    btn_e = ttk.Button(frame, text='East')
    btn_s = ttk.Button(frame, text='South')
    btn_w = ttk.Button(frame, text='West')

    CreateToolTip(btn_ne, "Testing if this works/nHello")
    CreateToolTip(btn_sw, 'Lorem ipsum dolor sit amet, velit eu nam cursus '
                     'quisque gravida sollicitudin, felis arcu interdum '
                     'error quam quis massa, et velit libero ligula est '
                     'donec. Suspendisse fringilla urna ridiculus dui '
                     'volutpat justo, quisque nisl eget sed blandit '
                     'egestas, libero nullam magna sem dui nam, auctor '
                     'vehicula nunc arcu vel sed dictum, tincidunt vitae '
                     'id tristique aptent platea. Lacus eros nec proin '
                     'morbi sollicitudin integer, montes suspendisse '
                     'augue lorem iaculis sed, viverra sed interdum eget '
                     'ut at pulvinar, turpis vivamus ac pharetra nulla '
                     'maecenas ut. Consequat dui condimentum lectus nulla '
                     'vitae, nam consequat fusce ac facilisis eget orci, '
                     'cras enim donec aenean sed dolor aliquam, elit '
                     'lorem in a nec fringilla, malesuada curabitur diam '
                     'nonummy nisl nibh ipsum. In odio nunc nec porttitor '
                     'ipsum, nunc ridiculus platea wisi turpis praesent '
                     'vestibulum, suspendisse hendrerit amet quis vivamus '
                     'adipiscing elit, ut dolor nec nonummy mauris nec '
                     'libero, ad rutrum id tristique facilisis sed '
                     'ultrices. Convallis velit posuere mauris lectus sit '
                     'turpis, lobortis volutpat et placerat leo '
                     'malesuada, vulputate id maecenas at a volutpat '
                     'vulputate, est augue nec proin ipsum pellentesque '
                     'fringilla. Mattis feugiat metus ultricies repellat '
                     'dictum, suspendisse erat rhoncus ultricies in ipsum, '
                     'nulla ante pellentesque blandit ligula sagittis '
                     'ultricies, sed tortor sodales pede et duis platea')


    r = 0
    c = 0
    pad = 10
    btn_nw.grid(row=r, column=c, padx=pad, pady=pad, sticky=tk.NW)
    btn_n.grid(row=r, column=c + 1, padx=pad, pady=pad, sticky=tk.N)
    btn_ne.grid(row=r, column=c + 2, padx=pad, pady=pad, sticky=tk.NE)

    r += 1
    btn_w.grid(row=r, column=c + 0, padx=pad, pady=pad, sticky=tk.W)
    btn_center.grid(row=r, column=c + 1, padx=pad, pady=pad,
                sticky=tk.NSEW)
    btn_e.grid(row=r, column=c + 2, padx=pad, pady=pad, sticky=tk.E)

    r += 1
    btn_sw.grid(row=r, column=c, padx=pad, pady=pad, sticky=tk.SW)
    btn_s.grid(row=r, column=c + 1, padx=pad, pady=pad, sticky=tk.S)
    btn_se.grid(row=r, column=c + 2, padx=pad, pady=pad, sticky=tk.SE)

    frame.grid(sticky=tk.NSEW)
    for i in (0, 2):
        frame.rowconfigure(i, weight=1)
        frame.columnconfigure(i, weight=1)

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    root.title('Tooltip')
    root.mainloop()