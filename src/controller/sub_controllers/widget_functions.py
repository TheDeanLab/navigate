import re

FLOAT_REGEX = '(^-?$)|(^-?[0-9]+\.?[0-9]*$)'
FLOAT_REGEX_NONNEGATIVE = '(^$)|(^-?[0-9]+\.?[0-9]*$)'

def validate_float_wrapper(widget, negative=False):
    def check_float(value):
        if negative:
            valid = re.match(FLOAT_REGEX, value) is not None
        else:
            valid = re.match(FLOAT_REGEX_NONNEGATIVE, value) is not None
        if negative and value == '-':
            widget.configure(foreground='red')
        elif valid and value:
            if widget['from'] and float(value) < widget['from']:
                widget.configure(foreground='red')
            elif widget['to'] and float(value) > widget['to']:
                valid = False
            else:
                widget.configure(foreground='black')
        return valid

    def show_error():
        widget.configure(foreground="red")
        if not re.match(FLOAT_REGEX, widget.get()):
            widget.set(0)

    widget.configure(validate='all', validatecommand=(widget.register(check_float), '%P'))
    widget.configure(invalidcommand=show_error)
