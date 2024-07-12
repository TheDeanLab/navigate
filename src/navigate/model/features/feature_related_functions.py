# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Third-party imports

# Local application imports
from navigate.model.features.auto_tile_scan import CalculateFocusRange  # noqa
from navigate.model.features.autofocus import Autofocus  # noqa
from navigate.model.features.adaptive_optics import TonyWilson  # noqa
from navigate.model.features.common_features import (
    ChangeResolution,  # noqa
    Snap,  # noqa
    WaitToContinue,  # noqa
    WaitForExternalTrigger,  # noqa
    LoopByCount,  # noqa
    PrepareNextChannel,  # noqa
    MoveToNextPositionInMultiPositionTable,  # noqa
    StackPause,  # noqa
    ZStackAcquisition,  # noqa
    FindTissueSimple2D,  # noqa
)
from navigate.model.features.image_writer import ImageWriter  # noqa
from navigate.model.features.restful_features import IlastikSegmentation  # noqa
from navigate.model.features.volume_search import VolumeSearch  # noqa
from navigate.model.features.remove_empty_tiles import (
    DetectTissueInStack,  # noqa
    DetectTissueInStackAndReturn, #noqa
    DetectTissueInStackAndRecord,  # noqa
    RemoveEmptyPositions,  # noqa
)
from navigate.tools.file_functions import load_yaml_file
from navigate.tools.common_functions import load_module_from_file


class SharedList(list):
    """Custom list class with a name attribute for sharing data.

    This class extends the built-in list class to provide an additional attribute
    called 'name' for identifying and sharing lists of data. It is particularly
    useful when sharing data between different parts of a program.

    Notes:
    ------
    - This class is designed to be used when you need to pass and share lists of
      data between different components of a program.
    - The '__name__' attribute can be used to give the shared list a meaningful
      name for easier identification.
    """

    def __init__(self, value, name=None):
        """
        Initialize a SharedList object.

        Parameters:
        ----------
        value : iterable, optional
            Initial values for the list (default is an empty list).
        name : str, optional
            A name to identify the shared list (default is 'shared_list__').
        """
        super().__init__(value)
        if name is None:
            name = "shared_list__"
        self.__name__ = name

    def __str__(self):
        """Return a string representation of the shared list.

        Returns:
        -------
        str
            A string containing the type, name, and current values of the shared
            list.

        Notes:
        ------
        The string representation is in the form of a dictionary with 'type',
        'name', and 'value' keys.
        """

        return str({"type": "shared_list", "name": self.__name__, "value": self})


def convert_str_to_feature_list(content: str):
    """Convert string to a feature list

    Parameters
    ----------
    content : str
        A string value that represents a feature list.

    Returns
    -------
    feature_list : List
        A list: If the string value can be converted to a valid feature list
        None: If can not.
    """

    def convert_args_to_tuple(feature_list):
        """Recursively convert 'args' within a feature list to tuples.

        This function takes a feature list, which is typically used for specifying
        configuration options, and ensures that all 'args' elements within the list
        are converted to tuples. It operates recursively to handle nested feature
        lists.

        Parameters:
        ----------
        feature_list : list
            The feature list to process. It can contain dictionaries with 'args'
            elements that need to be converted to tuples.

        Returns:
        -------
        None

        Notes:
        ------
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


def convert_feature_list_to_str(feature_list):
    """Convert a feature list to its string representation.

    This function takes a feature list, which is typically used for specifying
    configuration options, and converts it to its string representation. The
    resulting string can be useful for saving, displaying, or transmitting
    feature lists.

    Parameters:
    ----------
    feature_list : list
        A valid feature list.

    Returns:
    -------
    result : str
        The string representation of the feature list.

    Notes:
    ------
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

    Example:
    --------
    Given the following feature list:

    ```
    [
        {"name": func1, "args": (arg1, arg2)},
        {"name": func2},
        [
            {"name": func3, "args": (arg3,)},
            {"name": func4}
        ]
    ]
    ```

    The function would return the string representation:

    ```
    "[{'name': 'func1', 'args': ('arg1', 'arg2')}, {'name': 'func2'},
    [{'name': 'func3', 'args': ('arg3',)}, {'name': 'func4'}]]"
    ```
    """
    if feature_list == "break" or feature_list == "continue":
        return f'"{feature_list}"'

    result = "["

    def f(feature_list):
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
                        result += '"true":' + convert_feature_list_to_str(item["true"]) + ','
                if "false" in item:
                    if type(item["false"]) == str:
                        result += f'"false": "{item["false"]}",'
                    else:
                        result += '"false":' + convert_feature_list_to_str(item["false"]) + ','
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
):
    """Load dynamic parameter functions into a feature list.

    This function takes a feature list and a path to the parameter setting files
    and dynamically updates the feature list with parameter values specified in
    the setting files. It searches for parameter values in the setting files
    and replaces corresponding arguments in the feature list with the loaded
    values. The function is designed to support dynamic configuration of
    feature functions with external parameter files.

    Parameters:
    -----------
    feature_list : list
        A list of feature configurations, typically used for specifying
        configuration options. It may contain dictionaries with "name" and "args"
        keys, where "name" is the feature function and "args" is a tuple of
        arguments. Arguments that match parameter names specified in the setting
        files will be replaced with loaded values.

    feature_parameter_setting_path : str
        The path to the directory containing parameter setting files. These files
        should be named based on the feature function names (e.g., function_name.yml).

    Notes:
    ------
    - The function iterates through the feature list, inspecting each feature
      dictionary for parameter values specified in the setting files.
    - Parameters that match argument names in the feature list are replaced with
      the loaded values from the setting files.
    - The function supports loading parameter values from YAML files and
      dynamically updating the feature list.

    Example:
    --------
    Given a feature list and a parameter setting file:
    - feature_list:
      ```
      [
          {"name": func1, "args": (arg1, arg2)},
          {"name": func2},
          [
              {"name": func3, "args": (arg3,)},
              {"name": func4}
          ]
      ]
      ```
    - parameter setting file (func1.yml):
      ```
      arg1: value1
      arg2: value2
      ```

    The function would update the feature list as follows:
    ```
    [
        {"name": func1, "args": ("value1", "value2")},
        {"name": func2},
        [
            {"name": func3, "args": (arg3,)},
            {"name": func4}
        ]
    ]
    ```
    """
    for item in feature_list:
        if type(item) is dict:
            if "args" in item:
                feature = item["name"]
                config_path = (
                    f"{feature_parameter_setting_path}/{feature.__name__}.yml"
                )
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
