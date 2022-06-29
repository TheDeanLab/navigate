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
import re
import tkinter as tk
from tkinter import ttk        
from decimal import Decimal, InvalidOperation
from .hoverbar import Tooltip
from .LabelInputWidgetFactory import LabelInput
import logging
from pathlib import Path

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

REGEX_DICT = {
    'float': '(^-?$)|(^-?[0-9]+\.?[0-9]*$)',
    'float_nonnegative': '(^$)|(^[0-9]+\.?[0-9]*$)',
    'int': '^-?[0-9]*$',
    'int_nonnegative': '^[0-9]*$'
}

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
def someFun(): do something
def otherFun(): do something
widget = ttk.Entry()
wrapped_function = widget.register(someFun)
other_function = widget.register(otherFun)
validation_function = (wrapped_function, '%P') # Can use any amount of substitution codes above to pass in various data
invalid = (other_function, '%P', '%s')
widget.config(
            validate='all',
            validatecommand=validation_function with args,
            invalidcommand=invalid_function with args
)

'''

# Base Class
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
            validatecommand=(validcmd, '%P', '%s', '%S', '%V', '%i', '%d'), # pass in all sub codes/data
            invalidcommand=(invalidcmd, '%P', '%s', '%S', '%V', '%i', '%d')
        )

    # Error handler - where you can customize color or what happens to widget
    def _toggle_error(self, on=False):
        self.config(foreground=('red' if on else 'black')) # Changes text to red on error

    # Validation, args are the sub codes. This just sets up validation then runs based on event type
    def _validate(self, proposed, current, char, event, index, action):
        self._toggle_error(False) # Error is off
        self.error.set("") # No error to start
        valid=True # Again true means no error
        if event == 'focusout': # Leaving widget
            valid = self._focusout_validate(event=event)
        elif event == 'key': # Keystroke into widget
            valid = self._key_validate(proposed=proposed, current=current, char=char, event=event, index=index, action=action)
        return valid

    # Sub validation functions to be overridden by specific widgets
    def _focusout_validate(self, **kwargs): # **kwargs lets us just specify needed keywords or get args from **kwargs(double pointer ie array) rather than getting args in right order
        return True
    
    def _key_validate(self, **kwargs):
        return True

    # Invalid
    def _invalid(self, proposed, current, char, event, index, action):
        if event == 'focusout':
            self._focusout_invalid(event=event)
        elif event == 'key':
            self._key_invalid(proposed=proposed, current=current, char=char, event=event, index=index, action=action)
        
    def _focusout_invalid(self, **kwargs):
        self._toggle_error(True)
    
    def _key_invalid(self, **kwargs):
        pass
    
    # Allows a manual check on entered values to be used whenever needed
    def trigger_focusout_validation(self):
        valid = self._validate('', '', '', 'focusout', '', '')
        if not valid:
            self._focusout_invalid(event='focusout')
        return valid


# Entry class that requires Entry
# Can optionally pass in a precision, min value, max value and a boolean for whether the entry requires a value. The min_var, max_var and focus_update_var are the same as spinbox
class ValidatedEntry(ValidatedMixin, ttk.Entry):
    def __init__(self, *args, precision=0, required=False, min_var=None, max_var=None, focus_update_var=None, min='-Infinity', max='Infinity', **kwargs):
        super().__init__(*args, **kwargs)
        self.resolution = Decimal(precision) # Number for precision given on creation
        self.precision = (self.resolution.normalize().as_tuple().exponent) # Precision of number as exponent
        self.variable = kwargs.get('textvariable') or tk.StringVar
        self.min = min
        self.max = max
        self.required = required
        
    # Dynamic range checker
        if min_var:
            self.min_var = min_var
            self.min_var.trace('w', self._set_minimum)
        if max_var:
            self.max_var = max_var
            self.max_var.trace('w', self._set_maximum)
        self.focus_update_var = focus_update_var
        self.bind('<FocusOut>', self._set_focus_update_var)

    def _key_validate(self, char, index, current, proposed, action, **kwargs):

        valid = True
        min_val = self.min
        max_val = self.max

        # check if there are range limits
        # TODO: I add a line here, please make sure is it okay?
        if min_val == '-Infinity' or max_val == 'Infinity':
            return True

        no_negative = int(min_val) >= 0
        no_decimal = self.precision >= 0


        # Allow deletion
        if action == '0':
            return True

        # Testing keystroke for validity
        # Filter out obviously bad keystrokes
        if any([
            (char not in ('-1234567890.')),
            (char == '-' and (no_negative or index != '0')),
            (char == '.' and (no_decimal or '.' in current))
        ]):
            return False

        # Proposed is either a Decimal, '-', '.', or '-.' need one final check for '-' and '.' 
        if proposed in '-.':
            return True

        # Proposed value is a Decimal, so convert and check further
        proposed = Decimal(proposed)
        proposed_precision = proposed.as_tuple().exponent
        if any([
            (proposed > int(max_val)),
            (proposed_precision < self.precision)
        ]):
            return False
        
        return valid

    

    # If entry widget is empty set the error string and return False TODO add hover bubble with error message
    def _focusout_validate(self, event):
        valid = True
        value = self.get()
        max_val = self.max
        min_val = self.min
        # Check for error upon leaving widget
        # TODO: I add some lines here, please make sure are they okay?
        if value.strip() == '' and self.required:
            self.error.set('A value is required')
            return False
        else:
            self.error.set('')
        
        # check if there are range limits
        if min_val == '-Infinity' or max_val == 'Infinity':
            return True

        try:
            value = Decimal(value)
        except InvalidOperation:
            self.error.set('Invalid number string: {}'.format(value))
            return False
        
        # Checking if greater than minimum
        if value < int(min_val):
            self.error.set('Value is too low (min {})'.format(min_val))
            valid = False

        # Checking if less than max
        if value > int(max_val):
            self.error.set('Value is too high (max {})'.format(max_val))

        

        return valid
    
    # Gets current value of widget and if focus_update_var is present it sets it to the same value
    def _set_focus_update_var(self, event):
        value = self.get()
        if self.focus_update_var and not self.error.get():
            self.focus_update_var.set(value)
    
    # Update minimum based on given variable
    def _set_minimum(self, *args):
        current = self.get()
        try:
            new_min = self.min_var.get()
            self.min = new_min
            print(self.max)
            logger.info(self.max)
        except (tk.TclError, ValueError):
            pass
        if not current:
            self.delete(0, tk.END)
        else:
            self.variable.set(current)
        self.trigger_focusout_validation() # Revalidate with the new minimum
    
    # Update maximum based on given variable
    def _set_maximum(self, *args):
        current = self.get()
        try:
            new_max = self.max_var.get()
            self.max = new_max
        except (tk.TclError, ValueError):
            pass
        if not current:
            self.delete(0, tk.END)
        else:
            self.variable.set(current)
        self.trigger_focusout_validation() # Revalidate with the new maximum

# Clears box on backspace, allows fully typed words that match values to be accepted, and an option to require a value
class ValidatedCombobox(ValidatedMixin, ttk.Combobox):

    def _key_validate(self, proposed, action, **kwargs):
        valid = True
        # Clear field with delete or backspace
        if action == '0':
            self.set('')
            return True
        # Get list of combo values
        values = self.cget('values')
        # Check for words typed in if they match then set to that value
        matching = [
            x for x in values
            if x.lower().startswith(proposed.lower())
        ]
        if len(matching) == 0:
            valid = False
        elif len(matching) == 1:
            self.set(matching[0])
            self.icursor(tk.END)
            valid = False
        return valid

    # Require a value
    def _focusout_validate(self, **kwargs):
        valid = True
        if not self.get():
            valid = False
            self.error.set('A value is required')
        return valid


# Deletion always allowed, digits always allowed, if from < 0 '-' is allowed as first char, 
# if increment is decimal '.' allowed, if proposed value is greater than to ignore key
# if proposed value requires more precision than increment, ignore key
# On focusout, make sure number is a valid number string and greater than from value
# If given a min_var, max_var, or focus_update_var then the spinbox range will update dynamically when those valuse are changed (can be used to link to other widgets)
class ValidatedSpinbox(ValidatedMixin, ttk.Spinbox):
    def __init__(self, *args, precision=None, min_var=None, max_var=None, focus_update_var=None, from_='-Infinity', to='Infinity', **kwargs):
        super().__init__(*args, from_=from_, to=to, **kwargs)
        self.resolution = Decimal(str(kwargs.get('increment', '1.0'))) # Number put into spinbox
        self.precision = (self.resolution.normalize().as_tuple().exponent) # Precision of number as exponent
        self.variable = kwargs.get('textvariable') or tk.DoubleVar

        # Dynamic range checker
        if min_var:
            self.min_var = min_var
            self.min_var.trace('w', self._set_minimum)
        if max_var:
            self.max_var = max_var
            self.max_var.trace('w', self._set_maximum)
        self.focus_update_var = focus_update_var
        self.bind('<FocusOut>', self._set_focus_update_var)

    def set_precision(self, prec):
        '''
        Given a precision it will update the spinboxes ability to handle more or less precision for validation.
        This is separate from the increment value.
        '''
        self.precision = prec

    def _key_validate(self, char, index, current, proposed, action, **kwargs):

        valid = True
        min_val = self.cget('from')
        max_val = self.cget('to')
        no_negative = min_val >= 0
        no_decimal = self.precision >= 0


        # Allow deletion
        if action == '0':
            return True

        # Testing keystroke for validity
        # Filter out obviously bad keystrokes
        if any([
            (char not in ('-1234567890.')),
            (char == '-' and (no_negative or index != '0')),
            (char == '.' and (no_decimal or '.' in current))
        ]):
            return False

        # Proposed is either a Decimal, '-', '.', or '-.' need one final check for '-' and '.' 
        if proposed in '-.':
            return True

        # Proposed value is a Decimal, so convert and check further
        proposed = Decimal(proposed)
        proposed_precision = proposed.as_tuple().exponent
        if any([
            (proposed > max_val),
            (proposed_precision < self.precision)
        ]):
            return False
        
        return valid

    def _focusout_validate(self, **kwargs):
        valid = True
        value = self.get()
        max_val = self.cget('to')
        min_val = self.cget('from')
        # Check for error upon leaving widget
        try:
            value = Decimal(value)
        except InvalidOperation:
            self.error.set('Invalid number string: {}'.format(value))
            return False

        # Checking if greater than minimum
        if value < min_val:
            self.error.set('Value is too low (min {})'.format(min_val))
            valid = False

        # Checking if less than max
        if value > max_val:
            self.error.set('Value is too high (max {})'.format(max_val))

        return valid


     # Gets current value of widget and if focus_update_var is present it sets it to the same value
    def _set_focus_update_var(self, event):
        value = self.get()
        if self.focus_update_var and not self.error.get():
            self.focus_update_var.set(value)


    # Update minimum based on given variable
    def _set_minimum(self, *args):
        current = self.get()
        try:
            new_min = self.min_var.get()
            self.config(from_=new_min)
        except (tk.TclError, ValueError):
            pass
        if not current:
            self.delete(0, tk.END)
        else:
            self.variable.set(current)
        self.trigger_focusout_validation() # Revalidate with the new minimum

    
    # Update maximum based on given variable
    def _set_maximum(self, *args):
        current = self.get()
        try:
            new_max = self.max_var.get()
            self.config(to=new_max)
        except (tk.TclError, ValueError):
            pass
        if not current:
            self.delete(0, tk.END)
        else:
            self.variable.set(current)
        self.trigger_focusout_validation() # Revalidate with the new maximum

if __name__ == '__main__':



    root = tk.Tk()
    frame = ttk.Frame(root)

    val = ['Hello', "World", "Science"]
    evar = tk.DoubleVar()
    wvar = tk.DoubleVar()

    btn_ne = LabelInput(frame,
                            label_pos="top",
                            label='Dynamic Range Entry',
                            input_class=ValidatedEntry,
                            input_var=tk.StringVar,
                            input_args={"min":'0', "max":'25', "min_var":wvar, "max_var":evar}
    )
    btn_se = ValidatedCombobox(frame)
    btn_se['values'] = val
    btn_sw = ValidatedCombobox(frame)
    btn_sw['values'] = val
    btn_nw = ValidatedEntry(frame)

    btn_center = LabelInput(frame,
                            label_pos="top",
                            label='Dynamic Range Spinbox',
                            input_class=ValidatedSpinbox,
                            input_var=tk.DoubleVar,
                            input_args={"from_":'0', "to":'25', "increment": '1.0', "min_var":wvar, "max_var":evar}
    )
    # btn_center = ValidatedSpinbox(frame, min_var=wvar,max_var=evar)


    btn_n = LabelInput(frame,
                            label_pos="top",
                            label='Validated Entry (4-15)',
                            input_class=ValidatedEntry,
                            input_var=tk.StringVar,
                            input_args={"min":'4', "max":'15', 'precision':'2', 'required':True}
    )
    btn_e = ValidatedSpinbox(frame, from_=0,to=20,increment=1,min_var=wvar, focus_update_var=evar)
    btn_s = ValidatedCombobox()
    btn_s['values'] = val
    btn_w = ValidatedSpinbox(frame, from_=0,to=20,increment=1, max_var=evar, focus_update_var=wvar)


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

    bt = Tooltip(btn_center, text="Value is not between {} and {}".format(wvar.get(),evar.get()), wraplength=200)
    
    def get_val():
        left = wvar.get()
        right = evar.get()
        Tooltip(btn_center, text="Value is not between {} and {}".format(left,right), wraplength=200)
    bt.widget.bind('<<Increment>>', get_val)
    bt.widget.bind('<<Decrement>>', get_val)

    root.title('Validation Tests')
    root.mainloop()

    

