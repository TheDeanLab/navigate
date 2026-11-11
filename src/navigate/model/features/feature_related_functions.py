# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
#

# Standard library imports
import os
import inspect
import importlib
from collections.abc import Iterable
from typing import Optional, Union

# Third-party imports

# Local application imports
from navigate.model.features.auto_tile_scan import CalculateFocusRange  # noqa
from navigate.model.features.autofocus import Autofocus  # noqa
from navigate.model.features.adaptive_optics import TonyWilson  # noqa
from navigate.model.features.common_features import (
    Snap,  # noqa
    WaitToContinue,  # noqa
    WaitForExternalTrigger,  # noqa
    LoopByCount,  # noqa
    PrepareNextChannel,  # noqa
    MoveToNextPositionInMultiPositionTable,  # noqa
    StackPause,  # noqa
    ZStackAcquisition,  # noqa
    FindTissueSimple2D,  # noqa
    ProjectionMode,  # noqa
)
from navigate.model.features.image_writer import ImageWriter  # noqa
from navigate.model.features.restful_features import IlastikSegmentation  # noqa
from navigate.model.features.volume_search import (
    VolumeSearch,  # noqa
    VolumeSearch3D,  # noqa
)
from navigate.model.features.remove_empty_tiles import (
    DetectTissueInStack,  # noqa
    DetectTissueInStackAndReturn,  # noqa
    DetectTissueInStackAndRecord,  # noqa
    RemoveEmptyPositions,  # noqa
)
from navigate.model.features.update_setting import (
    ChangeResolution,  # noqa
    SetCameraParameters,  # noqa
    UpdateExperimentSetting,  # noqa
)

from navigate.tools.file_functions import load_yaml_file
from navigate.tools.common_functions import load_module_from_file


class SharedList(list):
    """Custom list class with a name attribute for sharing data.

    This class extends the built-in list class to provide an additional attribute
    called 'name' for identifying and sharing lists of data. It is particularly
    useful when sharing data between different parts of a program.

    Notes
    -----
    - This class is designed to be used when you need to pass and share lists of
      data between different components of a program.
    - The '__name__' attribute can be used to give the shared list a meaningful
      name for easier identification.
    """

    def __init__(self, value: Iterable, name: Optional[str] = None) -> None:
        """
        Initialize a SharedList object.

        Parameters
        ----------
        value : Iterable
            Initial values for the list (default is an empty list).
        name : Optional[str]
            A name to identify the shared list (default is ``shared_list__``).
        """
        super().__init__(value)
        if name is None:
            name = "shared_list__"
        self.__name__ = name

    def __str__(self) -> str:
        """Return a string representation of the shared list.

        Returns
        -------
        str
            A string containing the type, name, and current values of the shared
            list.

        Notes
        -----
        The string representation is in the form of a dictionary with 'type',
        'name', and 'value' keys.
        """

        return str({"type": "shared_list", "name": self.__name__, "value": self})


def convert_str_to_feature_list(content: str) -> Union[list, str, None]:
    """Convert string to a feature list

    Parameters
    ----------
    content : str
        A string value that represents a feature list.

    Returns
    -------
    feature_list : Union[list, str, None]

        - List : If the string value can be converted to a valid feature list
        - None : If the string value cannot be converted to a valid feature list
        - "break" : If the string value is "break"
        - "continue" : If the string value is "continue"
    """

    def convert_args_to_tuple(feature_list: list) -> None:
        """Recursively convert 'args' within a feature list to tuples.

        This function takes a feature list, which is typically used for specifying
        configuration options, and ensures that all 'args' elements within the list
        are converted to tuples. It operates recursively to handle nested feature
        lists.

        Parameters
        ----------
        feature_list : list
            The feature list to process. It can contain dictionaries with 'args'
            elements that need to be converted to tuples.

        Returns
        -------
        None

        Notes
        -----
        - This function operates in-place and does not return a new list.
        - It is useful for ensuring that 'args' elements within a feature list are
          of tuple type, as required by certain functions or processes.
        - The function does not modify elements that are not dictionaries or do not
          have an 'args' key.
        - It handles nested feature lists, converting 'args' in inner lists as well.
        """

        if not feature_list:
            return
        for item in feature_list:
            if type(item) is dict:
                if "args" in item and type(item["args"]) is not tuple:
                    item["args"] = (item["args"],)
            else:
                convert_args_to_tuple(item)

    if content in ["break", '"break"', "'break'"]:
        return "break"
    if content in ["continue", '"continue"', "'continue'"]:
        return "continue"
    try:
        exec_result = {}
        exec(f"result={content}", globals(), exec_result)
        if type(exec_result["result"]) is not list:
            print("Please make sure the feature list is a list!")
            return None
        # 'args' should be tuple
        convert_args_to_tuple(exec_result["result"])
        return exec_result["result"]
    except Exception as e:
        print("Can't build this feature list!", e)
        return None


def convert_feature_list_to_str(feature_list: list) -> str:
    """Convert a feature list to its string representation.

    This function takes a feature list, which is typically used for specifying
    configuration options, and converts it to its string representation. The
    resulting string can be useful for saving, displaying, or transmitting
    feature lists.

    Parameters
    ----------
    feature_list : list
        A valid feature list.

    Returns
    -------
    result : str
        The string representation of the feature list.

    Notes
    -----
    - The function recursively processes the input feature list, converting
      dictionaries, tuples, and lists to their corresponding string
      representations.
    - Within the resulting string, dictionaries are represented with keys
      "name" and "args" (if present), where "name" is the name of the feature
      function and "args" contains the arguments as a tuple.
    - Tuples and lists are represented using parentheses and square brackets,
      respectively.
    - This function is intended for converting feature lists to a format that
      can be easily saved to a file, transmitted over a network, or displayed
      to users.

    Examples
    --------
    Given feature functions ``func1`` through ``func4`` and string arguments:

    .. code-block:: python

        feature_list = [
            {"name": func1, "args": ("arg1", "arg2")},
            {"name": func2},
            [
                {"name": func3, "args": ("arg3",)},
                {"name": func4},
            ],
        ]

    The returned string contains the following text (shown on two lines for
    readability; the function does not insert a newline):

    .. code-block:: text

        [{"name": func1,"args": ("arg1","arg2",),},{"name": func2,},
        [{"name": func3,"args": ("arg3",),},{"name": func4,},],]
    """
    if feature_list == "break" or feature_list == "continue":
        return f'"{feature_list}"'

    result = "["

    def f(feature_list: list):
        """Recursively convert a feature list to its string representation."""
        if not feature_list:
            return
        nonlocal result
        for item in feature_list:
            if type(item) is dict:
                result += "{" + f'"name": {item["name"].__name__},'
                if "args" in item:
                    result += '"args": ('
                    for temp in item["args"]:
                        if temp is None:
                            result += "None,"
                        elif callable(temp):
                            result += f'"{temp.__name__}",'
                        elif type(temp) is str:
                            result += f'"{temp}",'
                        else:
                            result += f"{temp},"
                    result += "),"
                if "true" in item:
                    if type(item["true"]) == str:
                        result += f'"true": "{item["true"]}",'
                    else:
                        result += (
                            '"true":' + convert_feature_list_to_str(item["true"]) + ","
                        )
                if "false" in item:
                    if type(item["false"]) == str:
                        result += f'"false": "{item["false"]}",'
                    else:
                        result += (
                            '"false":'
                            + convert_feature_list_to_str(item["false"])
                            + ","
                        )
                result += "},"
            elif type(item) is tuple:
                result += "("
                f(item)
                result += "),"
            elif type(item) is list:
                result += "["
                f(item)
                result += "],"

    f(feature_list)
    result += "]"
    return result


def load_dynamic_parameter_functions(
    feature_list: list, feature_parameter_setting_path: str
) -> None:
    """Load dynamic parameter functions into a feature list in place.

    Resolve named function arguments using per-feature YAML settings. Each
    setting maps a parameter name to function names and their importable modules
    or Python source paths.

    Parameters
    ----------
    feature_list : list
        Feature dictionaries and nested lists or tuples. Each dictionary uses
        ``name`` for the feature class and optionally ``args`` for its positional
        arguments after ``self`` and ``model``. Matching argument names are
        replaced with loaded functions in the existing dictionaries.
    feature_parameter_setting_path : str
        Directory containing settings named ``<feature class name>.yml``.
        Features without a settings file are left unchanged.

    Notes
    -----
    A configured argument becomes ``None`` when its name is absent from the
    parameter's mapping or its mapped value is ``None`` or ``"None"``. Existing
    source paths are loaded as modules; other mapped strings are imported as
    module names. Nested lists and tuples are processed recursively, while
    ``"break"`` and ``"continue"`` entries are skipped.

    Examples
    --------
    Given a feature class with a dynamic function parameter:

    .. code-block:: python

        class ExampleFeature:
            def __init__(self, model, transform):
                self.transform = transform

        feature_list = [
            {"name": ExampleFeature, "args": ("sqrt",)},
        ]

    Store the following in ``ExampleFeature.yml`` in the settings directory:

    .. code-block:: yaml

        transform:
            sqrt: math

    Loading these settings replaces the string argument with ``math.sqrt``:

    .. code-block:: python

        load_dynamic_parameter_functions(feature_list, settings_directory)
        # feature_list[0]["args"] is now (math.sqrt,).
    """
    if not feature_list:
        return
    for item in feature_list:
        if type(item) is dict:
            if "args" in item:
                feature = item["name"]
                config_path = f"{feature_parameter_setting_path}/{feature.__name__}.yml"
                parameter_config = None
                if os.path.exists(config_path):
                    parameter_config = load_yaml_file(config_path)
                if parameter_config:
                    args = list(item["args"])
                    spec = inspect.getfullargspec(feature)
                    for parameter in parameter_config:
                        idx = spec.args[2:].index(parameter)
                        if idx >= len(args):
                            continue
                        if args[idx] is None:
                            args[idx] = "None"
                        if args[idx] not in parameter_config[parameter]:
                            ref_lib = None
                        else:
                            ref_lib = parameter_config[parameter][args[idx]]
                        if ref_lib is None or ref_lib == "None":
                            args[idx] = None
                        elif os.path.exists(ref_lib):
                            module = load_module_from_file(args[idx], ref_lib)
                            args[idx] = getattr(module, args[idx]) if module else None
                        else:
                            module = importlib.import_module(ref_lib)
                            args[idx] = getattr(module, args[idx]) if module else None
                    item["args"] = tuple(args)
        elif item == "break" or item == "continue":
            continue
        else:
            load_dynamic_parameter_functions(item, feature_parameter_setting_path)
