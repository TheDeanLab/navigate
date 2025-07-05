# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import platform
import logging
import time
import importlib
from multiprocessing.managers import ListProxy
from typing import Callable, Tuple, Any, Type, Dict, Optional

# Third Party Imports

# Local Imports
from navigate.tools.common_functions import build_ref_name, load_param_from_module
from navigate.model.devices.device_types import (
    SerialDevice,
    IntegratedDevice,
    NIDevice,
    SequenceDevice,
)
from navigate.model.devices.daq.base import DAQBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class DummyDeviceConnection:
    """Dummy Device"""

    pass


def auto_redial(
    func: Callable[..., Any],
    args: Tuple[Any, ...],
    n_tries: int = 10,
    exception: Type[Exception] = Exception,
    **kwargs: Any,
) -> Any:
    """Retries connections to a startup device defined by `func` for a specified
    number of attempts.

    This function attempts to execute the connection function `func` up to `n_tries`
    times. If an exception occurs, it retries the connection after a brief pause,
    logging each failure. If the connection partially succeeds, it cleans up any objects
    before retrying.

    Parameters
    ----------
    func : Callable[..., Any]
        The function or class (`__init__()` method) that connects to a device.
    args : Tuple[Any, ...]
        Positional arguments to pass to the `func`.
    n_tries : int
        The number of attempts to retry the connection. Default is 10.
    exception : Type[Exception]
        The exception type to catch and handle during connection attempts.
        Default is `Exception`.
    **kwargs : Any
        Additional keyword arguments passed to `func`.

    Returns
    -------
    Any
        The result of the successful execution of `func`.

    Raises
    ------
    exception
        If all connection attempts fail, the specified `exception` is raised.
    """
    val = None

    for i in range(n_tries):
        try:
            val = func(*args, **kwargs)
        except exception as e:
            if i < (n_tries - 1):
                logger.debug(
                    f"auto_redial - Failed {str(func)} attempt {i+1}/{n_tries} "
                    f"with exception {e}."
                )
                # If we failed, but part way through object creation, we must
                # delete the object prior to trying again. This lets us restart
                # the connection process with a clean slate
                if val is not None:
                    val.__del__()
                    del val
                    val = None
                time.sleep(0.5)  # TODO: 0.5 reached by trial and error. Better value?
            else:
                logger.error(f"Device startup failed: {e}")
                raise exception
        else:
            break

    return val


class SerialConnectionFactory:
    """Serial Connection Factory.

    This class is used to build serial connections to devices.
    """

    _connections = {}

    @classmethod
    def build_connection(
        cls,
        build_connection_function: Callable[..., Any],
        args: Tuple[Any, ...],
        exception: Type[Exception] = Exception,
    ) -> Any:
        """
        Builds a serial connection to a device.

        This method establishes a connection to a device using the provided
        connection-building function and arguments. If the connection does not exist,
        it will be created and stored.

        Parameters
        ----------
        build_connection_function : Callable
            Function that builds the connection to the device.
        args : Tuple
            Arguments to the build_connection_function
        exception : Type[Exception]
            Exception to catch when building the connection

        Returns
        -------
        connection : Any
            Connection to the device

        Raises
        ------
        exception : Exception
            If the connection building process fails, the specified `exception` is
            raised.
        """
        port = args[0]
        if str(port) not in cls._connections:
            cls._connections[str(port)] = auto_redial(
                build_connection_function, args, exception=exception
            )

        return cls._connections[str(port)]


class IntegratedDeviceFactory:
    """Integrated Device Factory.

    This class is used to build integrated device connections.
    """

    _connections = {}

    @classmethod
    def build_connection(
        cls,
        unique_id: str,
        build_connection_function: Callable[..., Any],
        args: Tuple[Any, ...],
        exception: Type[Exception] = Exception,
    ) -> Any:
        """
        Builds an integrated device connection.

        This method establishes a connection to an integrated device using the provided
        connection-building function and arguments. If the connection does not exist, it
        will be created and stored.

        Parameters
        ----------
        unique_id : str
            Unique identifier for the device
        build_connection_function : Callable
            Function that builds the connection to the device.
        args : Tuple
            Arguments to the build_connection_function
        exception : Type[Exception]
            Exception to catch when building the connection

        Returns
        -------
        connection : Any
            Connection to the device

        Raises
        ------
        exception : Exception
            If the connection building process fails, the specified `exception` is
            raised.
        """
        if str(unique_id) not in cls._connections:
            cls._connections[str(unique_id)] = auto_redial(
                build_connection_function, args, exception=exception
            )

        return cls._connections[str(unique_id)]


class SequenceDeviceFactory:
    """Sequence Device Factory.

    This class is used to build sequence device connections.
    """

    _connections = {}

    @classmethod
    def build_connection(
        cls,
        unique_id: str,
        build_connection_function: Callable[..., Any],
        args: Tuple[Any, ...],
        exception: Type[Exception] = Exception,
        max_device_num: int = 2,
    ) -> Any:
        """
        Builds a sequence device connection.

        This method establishes a connection to a sequence device using the provided
        connection-building function and arguments. If the connection does not exist, it
        will be created and stored.

        Parameters
        ----------
        unique_id : str
            Unique identifier for the device
        build_connection_function : Callable
            Function that builds the connection to the device.
        args : Tuple
            Arguments to the build_connection_function
        exception : Type[Exception]
            Exception to catch when building the connection
        max_device_num : int
            Maximum number of devices to connect to. Default is 2.

        Returns
        -------
        connection : Any
            Connection to the device

        Raises
        ------
        exception : Exception
            If the connection building process fails, the specified `exception` is
            raised.
        """
        device_type, serial_number = unique_id.split("_")
        if device_type not in cls._connections:
            cls._connections[device_type] = {}

        if str(serial_number) in cls._connections[device_type]:
            return cls._connections[device_type][str(serial_number)]

        for i in range(len(cls._connections[device_type].keys()), max_device_num):
            device = auto_redial(build_connection_function, (i,), exception=exception)
            cls._connections[device_type][device._serial_number] = device
            if device._serial_number[0] == "0":
                try:
                    oct_num = int(device._serial_number, 8)
                    cls._connections[device_type][str(oct_num)] = device
                except ValueError:
                    logger.debug("Error converting device serial number to octal")
                    pass
            if str(serial_number) in cls._connections[device_type]:
                return cls._connections[device_type][str(serial_number)]

        raise device_not_found(device_type, serial_number)


def start_device(
    microscope_name: str,
    configuration: Dict[str, Any],
    device_category: str,
    device_id: int = 0,
    is_synthetic: bool = False,
    daq_connection: Optional[Any] = None,
    plugin_devices: Optional[Dict] = None,
) -> Any:
    """Starts a device.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    configuration : Dict[str, Any]
        Global configuration of the microscope
    device_category : str
        Type of device to connect to, such as stage, camera, filter_wheel, etc.
    device_id : int
        Index of device in the configuration dictionary. Default is 0.
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    daq_connection: Optional[Any]
        Data acquisition connection. Default is None.
    plugin_devices : Optional[Dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    device : Any
        Device class.
    """
    if plugin_devices is None:
        plugin_devices = {}

    device_config = configuration["configuration"]["microscopes"][microscope_name][
        device_category
    ]

    if device_category == "stage":
        device_config = device_config["hardware"]

    if type(device_config) == ListProxy:
        device_config = device_config[device_id]

    if device_category != "stage":
        device_config = device_config["hardware"]

    device_type = device_config["type"]

    if "_" in device_category:
        class_name_suffix = "".join(
            [x.capitalize() for x in device_category.split("_")]
        )
    else:
        class_name_suffix = device_category.capitalize()

    device_types_dict = load_param_from_module(
        "navigate.config.configuration_database", device_category + "_device_types"
    )

    for k in device_types_dict:
        if type(device_types_dict[k]) is not tuple:
            device_types_dict[k] = (device_types_dict[k], device_types_dict[k])

    temp_device_ref = dict(device_types_dict.values())

    if is_synthetic or device_type.lower().startswith("synthetic"):
        device_type = "Synthetic"
    elif device_type.endswith(class_name_suffix):
        device_type = device_type[: -len(class_name_suffix)]

    # device type naming rules: manufacturer(file_name).device_model
    # if the device is currently supported in Navigate, you can use device_model as the
    # device type.
    if "." in device_type:
        device_manufacturer, device_type = device_type.split(".")[:2]
    elif device_type in temp_device_ref:
        device_manufacturer = temp_device_ref[device_type]
    else:
        device_manufacturer = None

    if device_manufacturer is not None and importlib.util.find_spec(
        f"navigate.model.devices.{device_category}.{device_manufacturer}"
    ):
        module = importlib.import_module(
            f"navigate.model.devices.{device_category}.{device_manufacturer}"
        )
        try:
            _class = getattr(module, device_type + class_name_suffix)
        except (KeyError, AttributeError):
            logger.error(
                f"There is no device class {device_type + class_name_suffix} in the file: {device_manufacturer}.py"
            )
            return device_not_found(
                microscope_name, device_category, device_type, device_id
            )

        # Load serial devices via the SerialDevice factory.
        if issubclass(_class, SerialDevice):
            device_connection = SerialConnectionFactory.build_connection(
                _class.connect,
                (
                    device_config["port"],
                    device_config.get("baudrate", 115200),
                    device_config.get("timeout", 0.25),
                ),
                exception=Exception,
            )

        # Load integrated devices via the IntegratedDevice factory.
        elif issubclass(_class, IntegratedDevice):
            # get connection parameters
            connection_params = []
            for param in _class.get_connect_params():
                connection_params.append(device_config[param])
            # build connection
            device_connection = IntegratedDeviceFactory.build_connection(
                build_ref_name(
                    "_",
                    device_manufacturer,
                    device_type,
                    device_config.get("serial_number", "000000"),
                ),
                _class.connect,
                connection_params,
                exception=Exception,
            )
        elif issubclass(_class, SequenceDevice):
            # get connection parameters
            connection_params = []
            if hasattr(_class, "get_connect_params"):
                for param in _class.get_connect_params():
                    connection_params.append(device_config[param])
            # build connection
            device_connection = SequenceDeviceFactory.build_connection(
                build_ref_name(
                    "_", device_category, device_config.get("serial_number", "000000")
                ),
                _class.connect,
                args=connection_params,
                exception=Exception,
            )
        elif hasattr(_class, "connect"):
            # get connection parameters
            connection_params = []
            if hasattr(_class, "get_connect_params"):
                for param in _class.get_connect_params():
                    connection_params.append(device_config[param])
            device_connection = auto_redial(
                _class.connect, connection_params, exception=Exception
            )
        else:
            device_connection = None

        if issubclass(_class, NIDevice):
            if device_connection is None:
                device_connection = daq_connection
            else:
                device_connection = {
                    "connection": device_connection,
                    "daq_connection": daq_connection,
                }

        return _class(microscope_name, device_connection, configuration, device_id)

    elif device_category in plugin_devices:
        # device_category in ["stage", "shutter", "filter_wheel", "remote_focus", "camera", "galvo", "zoom", "laser"]
        if device_category == "stage":
            hardware_configuration = configuration["configuration"]["microscopes"][
                microscope_name
            ][device_category]["hardware"][device_id]
        else:
            hardware_configuration = configuration["configuration"]["microscopes"][
                microscope_name
            ][device_category][device_id]["hardware"]
        # find the device in plugins
        if device_type + class_name_suffix in plugin_devices[device_category]:
            device_type += class_name_suffix
        elif device_type not in plugin_devices[device_category]:
            device_not_found(microscope_name, device_category, device_type, device_id)

        try:

            device_connection = plugin_devices[device_category][device_type][
                "load_device"
            ](
                hardware_configuration,
                is_synthetic,
                device_type=device_category,
            )
            start_function = plugin_devices[device_category][device_type][
                "start_device"
            ]
            return start_function(
                microscope_name,
                device_connection,
                configuration,
                is_synthetic=is_synthetic,
                id=device_id,
                device_type=device_category,
            )
        except RuntimeError:
            print(
                f"{device_category}:{device_type} can't be loaded correctly, "
                f"make sure you have specify SUPPORTED_DEVICE_TYPES in your plugin!"
            )
    device_not_found(microscope_name, device_category, device_type, device_id)


def start_daq(
    configuration: Dict[str, Any], device_type: str = "NI", name: str = "name"
) -> DAQBase:
    """Initializes the data acquisition (DAQ) class on a dedicated thread.

    Load daq information from the configuration file. Proper daq types include NI and
    SyntheticDAQ.

    Parameters
    ----------
    configuration : Dict[str, Any]
        Global configuration
    device_type : str
        Type of device to connect to. Default is "NI".

    Returns
    -------
    DAQ : DAQBase
        DAQ class.
    """

    if device_type == "NI":
        from navigate.model.devices.daq.ni import NIDAQ

        return NIDAQ(configuration)

    elif device_type == "asi.ASI":
        # from navigate.model.devices.daq.asi import ASIDaq
        # name = "Microscope-0"
        return start_device(name, configuration, "daq")

    elif device_type.lower().startswith("synthetic"):
        from navigate.model.devices.daq.synthetic import SyntheticDAQ

        return SyntheticDAQ(configuration)

    else:
        device_not_found("DAQ", device_type)


def device_not_found(*args: Any) -> None:
    """
    Display an error message and raise an exception if the device is not found.

    This function logs an error message and raises a `RuntimeError` when the
    specified device cannot be found in the configuration or the configuration is
    incorrect.

    Parameters
    ----------
    args : tuple
        A list of arguments representing the device details. These are typically:

        - microscope_name (str): The name of the microscope.
        - device (str): The name of the device.
        - device id (int): The ID of the device.
        - device type (str): The type of the device.

    Raises
    ------
    RuntimeError
        If the device cannot be found or the configuration is incorrect.
    """
    error_statement = f"Device not found in configuration: {args}"
    logger.error(error_statement)
    print(error_statement)
    raise RuntimeError()


def load_devices(
    microscope_name: str,
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    devices_dict: dict = {},
    plugin_devices: Optional[dict] = None,
) -> dict:
    """Load devices from configuration.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    configuration : Dict[str, Any]
        Configuration dictionary
    is_synthetic : bool
        Run synthetic version of hardware?
    devices_dict : dict
        Dictionary of devices to load
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    devices : dict
        Dictionary of devices
    """

    if plugin_devices is None:
        plugin_devices = {}

    # start daq
    if "daq" not in devices_dict:
        devices_dict["daq"] = {}
    if is_synthetic:
        device_type = "Synthetic"
    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "daq"
        ]["hardware"]["type"]

    if device_type not in devices_dict["daq"]:
        devices_dict["daq"][device_type] = start_daq(configuration, device_type, microscope_name)

    return devices_dict
