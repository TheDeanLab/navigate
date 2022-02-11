import re
from traceback import format_exception

FLOAT_REGEX = '(^-?$)|(^-?[0-9]+\.?[0-9]*$)'
FLOAT_REGEX_NONNEGATIVE = '(^$)|(^-?[0-9]+\.?[0-9]*$)'

def validate_float_wrapper(widget, negative=False, is_entry=False):
    def check_range_spinbox(value):
        valid = True
        if widget['from'] and float(value) < widget['from']:
            widget.configure(foreground='red')
        elif widget['to'] and float(value) > widget['to']:
            valid = False
        else:
            widget.configure(foreground='black')
        return valid

    def check_range_entry(value):
        valid = True
        if widget.from_ and float(value) < widget.from_:
            widget.configure(foreground='red')
        elif widget.to and float(value) > widget.to:
            valid = False
        else:
            widget.configure(foreground='black')
        return valid
    
    if is_entry:
        check_range_func = check_range_entry
    else:
        check_range_func = check_range_spinbox
        
    def check_float(value):
        if negative:
            valid = re.match(FLOAT_REGEX, value) is not None
        else:
            valid = re.match(FLOAT_REGEX_NONNEGATIVE, value) is not None
        if negative and value == '-':
            widget.configure(foreground='red')
        elif valid and value:
            valid = check_range_func(value)
        return valid

    def show_error_func(is_entry=False):
        def func():
            widget.configure(foreground="red")
            if not re.match(FLOAT_REGEX, widget.get()):
                widget.set(0)
        def entry_func():
            widget.configure(foreground="red")
            if not re.match(FLOAT_REGEX, widget.get()):
                widget.delete(0, len(widget.get()))
                widget.insert(0, 0)

        if is_entry:
            return entry_func
        else:
            return func

    if is_entry:
        widget.from_ = None
        widget.to = None

    widget.configure(validate='all', validatecommand=(widget.register(check_float), '%P'))
    widget.configure(invalidcommand=show_error_func(is_entry))
