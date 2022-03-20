import tkinter as tk
from tkinter import ttk

# Base design courtesy of below book.
# Learning Path: Python GUI Programming - A Complete Reference Guide by Alan D. Moore and B. M. Harwani 
'''
The below classes take advantage of multiple inheritance to achieve validation.

Validation Events: none, focusin, focusout, focus, key, all
- Focus is whether user is using widget
- Key is when user is typing keystrokes

Substitution Codes for validation in tkinter: %P, %s, %i, %S, %v, %V, %W, %d
- %P = proposed value from user
- %s = value currently in field
- %i = index of text being edited. String
- %S = text being inserted or deleted
- %v = widgets validate value
- %V = event that triggered validation
- %W = widgets name in TK as string
- %d = code that indicates action attempted. 0 for delete, 1 for insert, -1 for other. String

Tkinter Validation process:
- validate sets the event that triggers callback
- validatecommand takes in command that determines if data is valid
- invalidcommand runs command given if validatecommand is False

A python callable is passed to a .register function for the widget
widget = ttk.Entry()
widget.config(
            validate='all',
            validatecommand
)

'''
class ValidatedMixin:
    '''
    #### Adds validation functionality to an input widget
    '''
    # error_var can be passed a var for error message, if not class creates its own
    def __init__(self, *args, error_var=None, **kwargs):
        self.error = error_var or tk.StringVar()
        super().__init__(*args, **kwargs) # Calls base class that is mixed in with this class

        # Validation setup
        validcmd = self.register(self._validate)
        invalidcmd = self.register(self._invalid)

        # Tkinter widget validation setup
        self.config(
            validate='all', # Includes all validation events keystroke and focus
            validatecommand=(validcmd, '%P', )
        )