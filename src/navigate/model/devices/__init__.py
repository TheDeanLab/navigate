""" Hardware devices. """

# Standard library imports
from functools import wraps
import logging
import reprlib

# Third party imports

# Local imports
# from .daq.synthetic import SyntheticDAQ  # noqa
# from .camera.synthetic import SyntheticCamera  # noqa
# from .filter_wheel.synthetic import SyntheticFilterWheel  # noqa
# from .galvo.synthetic import SyntheticGalvo  # noqa
# from .remote_focus.synthetic import SyntheticRemoteFocus  # noqa
# from .shutter.synthetic import SyntheticShutter  # noqa
# from .stages.synthetic import SyntheticStage  # noqa
# from .zoom.synthetic import SyntheticZoom  # noqa
# from .lasers.synthetic import SyntheticLaser  # noqa
# from .mirrors.synthetic import SyntheticMirror  # noqa

def log_initialization(cls):
    """Decorator for logging the initialization of a device class.

    Parameters
    ----------
    cls : class
        The class to be logged.

    Returns
    -------
    cls : class
        The class with the logging decorator.
    """
    # Set up the reprlib object
    mod_repr = reprlib.Repr()
    mod_repr.indent = 4
    mod_repr.maxstring = 50
    mod_repr.maxother = 50

    # Get the original __init__ method
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        module_location = cls.__module__
        logger = logging.getLogger(module_location.split(".")[1])
        try:
            original_init(self, *args, **kwargs)
            logger.info(f"{mod_repr.repr(cls.__name__)}, "
                        f"{mod_repr.repr(args)}, "
                        f"{mod_repr.repr(kwargs)}"
                        )
        except Exception as e:
            logger.error(f"{mod_repr.repr(cls.__name__)} Initialization Failed")
            logger.error(f"Input args & kwargs: {args}, {kwargs}")
            logger.error(f"Error: {e}")
            raise e

    # Replace the original __init__ method with the new one
    cls.__init__ = new_init
    return cls