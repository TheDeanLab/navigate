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
from navigate.tools.common_functions import build_ref_name
from navigate.model.devices.camera.base import CameraBase
from navigate.model.devices.daq.base import DAQBase
from navigate.model.devices.filter_wheel.base import FilterWheelBase
from navigate.model.devices.galvo.base import GalvoBase
from navigate.model.devices.lasers.base import LaserBase
from navigate.model.devices.mirrors.base import MirrorBase
from navigate.model.devices.shutter.base import ShutterBase
from navigate.model.devices.stages.base import StageBase
from navigate.model.devices.remote_focus.base import RemoteFocusBase
from navigate.model.devices.zoom.base import ZoomBase

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


def load_camera_connection(
    configuration: Dict[str, Any], camera_id: int = 0, is_synthetic: bool = False
) -> Any:
    """Initialize the camera API class.

    Load camera information from the configuration file. Proper camera types include
    HamamatsuOrca, HamamatsuOrcaLightning, Photometrics, and SyntheticCamera.

    Parameters
    ----------
    configuration : Dict[str, Any]
        Global configuration of the microscope
    camera_id : int
        Device ID (0, 1...)
    is_synthetic: bool
        Whether it is a synthetic hardware

    Returns
    -------
    Camera_controller: Any
        The initialized camera API class instance.
    """

    if is_synthetic:
        cam_type = "SyntheticCamera"
    else:
        cam_type = configuration["configuration"]["hardware"]["camera"][camera_id][
            "type"
        ]

    if cam_type in [
        "HamamatsuOrca",
        "HamamatsuOrcaLightning",
        "HamamatsuOrcaFire",
        "HamamatsuOrcaFusion",
    ]:
        # Locally Import Hamamatsu API and Initialize Camera Controller
        HamamatsuController = importlib.import_module(
            "navigate.model.devices.APIs.hamamatsu.HamamatsuAPI"
        )
        return auto_redial(HamamatsuController.DCAM, (camera_id,), exception=Exception)

    elif cam_type.lower() == "syntheticcamera" or cam_type.lower() == "synthetic":
        from navigate.model.devices.camera.synthetic import (
            SyntheticCameraController,
        )

        return SyntheticCameraController()

    elif cam_type == "Photometrics":
        from navigate.model.devices.camera.photometrics import (
            build_photometrics_connection,
        )

        camera_connection = configuration["configuration"]["hardware"]["camera"][
            camera_id
        ]["camera_connection"]
        return auto_redial(
            build_photometrics_connection, (camera_connection,), exception=Exception
        )
    else:
        device_not_found("camera", camera_id, cam_type)


def start_camera(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: dict = None,
) -> CameraBase:
    """Initialize the camera class.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : dict
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Camera : CameraBase
        Instantiated camera class.
    """
    if plugin_devices is None:
        plugin_devices = {}

    if device_connection is None:
        device_not_found(microscope_name, "camera")

    if is_synthetic:
        cam_type = "SyntheticCamera"
    else:
        cam_type = configuration["configuration"]["microscopes"][microscope_name][
            "camera"
        ]["hardware"]["type"]

    if cam_type == "HamamatsuOrca":
        from navigate.model.devices.camera.hamamatsu import HamamatsuOrca

        return HamamatsuOrca(microscope_name, device_connection, configuration)

    elif cam_type == "HamamatsuOrcaLightning":
        from navigate.model.devices.camera.hamamatsu import HamamatsuOrcaLightning

        return HamamatsuOrcaLightning(microscope_name, device_connection, configuration)

    elif cam_type == "HamamatsuOrcaFire":
        from navigate.model.devices.camera.hamamatsu import HamamatsuOrcaFire

        return HamamatsuOrcaFire(microscope_name, device_connection, configuration)

    elif cam_type == "HamamatsuOrcaFusion":
        from navigate.model.devices.camera.hamamatsu import HamamatsuOrcaFusion

        return HamamatsuOrcaFusion(microscope_name, device_connection, configuration)

    elif cam_type == "Photometrics":
        from navigate.model.devices.camera.photometrics import PhotometricsBase

        return PhotometricsBase(microscope_name, device_connection, configuration)

    elif cam_type.lower() == "syntheticcamera" or cam_type.lower() == "synthetic":
        from navigate.model.devices.camera.synthetic import SyntheticCamera

        return SyntheticCamera(microscope_name, device_connection, configuration)

    elif "camera" in plugin_devices:
        for start_function in plugin_devices["camera"]["start_device"]:
            try:
                return start_function(
                    microscope_name,
                    device_connection,
                    configuration,
                    is_synthetic,
                    device_type="camera",
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "camera", cam_type)
    else:
        device_not_found(microscope_name, "camera", cam_type)


def load_mirror(configuration: Dict[str, Any], is_synthetic: bool = False) -> Any:
    """Initializes the deformable mirror API.

    Parameters
    ----------
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.

    Returns
    -------
    mirror : Any
        Instantiated .
    """
    if is_synthetic:
        mirror_type = "SyntheticMirror"
    else:
        mirror_type = configuration["configuration"]["hardware"]["mirror"]["type"]

    if mirror_type == "ImagineOpticsMirror":
        from navigate.model.devices.APIs.imagineoptics.imop import IMOP_Mirror

        return auto_redial(IMOP_Mirror, (), exception=Exception)

    elif mirror_type == "SyntheticMirror":
        return DummyDeviceConnection()

    else:
        device_not_found("mirror", mirror_type)


def start_mirror(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: Optional[Dict] = None,
) -> MirrorBase:
    """Initialize the mirror class.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[Dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    mirror : Any
        Mirror class.
    """
    if plugin_devices is None:
        plugin_devices = {}
    if device_connection is None or is_synthetic:
        mirror_type = "SyntheticMirror"

    else:
        mirror_type = configuration["configuration"]["microscopes"][microscope_name][
            "mirror"
        ]["hardware"]["type"]

    if mirror_type == "ImagineOpticsMirror":
        from navigate.model.devices.mirrors.imop import ImagineOpticsMirror

        return ImagineOpticsMirror(microscope_name, device_connection, configuration)

    elif mirror_type == "SyntheticMirror":
        from navigate.model.devices.mirrors.synthetic import SyntheticMirror

        return SyntheticMirror(microscope_name, device_connection, configuration)

    elif "mirror" in plugin_devices:
        return plugin_devices["mirror"]["start_device"](
            microscope_name, device_connection, configuration
        )

    else:
        device_not_found(microscope_name, "mirror", mirror_type)


def load_stages(
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: Optional[Dict] = None,
) -> Any:
    """Initialize the stage API.

    Stage information is pulled from the configuration file. Proper stage types include
    PI, MP285, Thorlabs, MCL, ASI, GalvoNIStage, and SyntheticStage.

    Parameters
    ----------
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[Dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Stage : Any
        Stage class.
    """
    if plugin_devices is None:
        plugin_devices = {}

    stage_devices = []

    stages = configuration["configuration"]["hardware"]["stage"]

    if type(stages) != ListProxy:
        stages = [stages]

    for i in range(len(stages)):
        stage_config = configuration["configuration"]["hardware"]["stage"][i]
        if is_synthetic:
            stage_type = "SyntheticStage"

        else:
            stage_type = stage_config["type"]

        if stage_type == "PI" and platform.system() == "Windows":
            from navigate.model.devices.stages.pi import build_PIStage_connection
            from pipython.pidevice.gcserror import GCSError

            stage_devices.append(
                auto_redial(
                    build_PIStage_connection,
                    (
                        stage_config["controllername"],
                        stage_config["serial_number"],
                        stage_config["stages"],
                        stage_config["refmode"],
                    ),
                    exception=GCSError,
                )
            )

        elif stage_type == "MP285" and platform.system() == "Windows":
            from navigate.model.devices.stages.sutter import (
                build_MP285_connection,
            )

            stage_devices.append(
                SerialConnectionFactory.build_connection(
                    build_MP285_connection,
                    (
                        stage_config["port"],
                        stage_config["baudrate"],
                        stage_config["timeout"],
                    ),
                    exception=UserWarning,
                )
            )

        elif stage_type == "Thorlabs" and platform.system() == "Windows":
            from navigate.model.devices.stages.tl_kcube_inertial import (
                build_TLKIMStage_connection,
            )
            from navigate.model.devices.APIs.thorlabs.kcube_inertial import (
                TLFTDICommunicationError,
            )

            stage_devices.append(
                auto_redial(
                    build_TLKIMStage_connection,
                    (stage_config["serial_number"],),
                    exception=TLFTDICommunicationError,
                )
            )

        elif stage_type == "KST101":
            from navigate.model.devices.stages.tl_kcube_steppermotor import (
                build_TLKSTStage_connection,
            )

            stage_devices.append(
                auto_redial(
                    build_TLKSTStage_connection,
                    (stage_config["serial_number"],),
                    exception=Exception,
                )
            )

        elif stage_type == "MCL" and platform.system() == "Windows":
            from navigate.model.devices.stages.mcl import (
                build_MCLStage_connection,
            )
            from navigate.model.devices.APIs.mcl.madlib import MadlibError

            stage_devices.append(
                auto_redial(
                    build_MCLStage_connection,
                    (stage_config["serial_number"],),
                    exception=MadlibError,
                )
            )

        elif stage_type == "ASI" and platform.system() == "Windows":
            """Filter wheel can be controlled from the same Tiger Controller. If
            so, then we will load this as a shared device. If not, we will create the
            connection to the Tiger Controller.
            """
            from navigate.model.devices.stages.asi import (
                build_ASI_Stage_connection,
            )
            from navigate.model.devices.APIs.asi.asi_tiger_controller import (
                TigerException,
            )

            stage_devices.append(
                SerialConnectionFactory.build_connection(
                    build_ASI_Stage_connection,
                    (
                        stage_config["port"],
                        stage_config["baudrate"],
                    ),
                    exception=TigerException,
                )
            )

        elif stage_type == "MS2000" and platform.system() == "Windows":
            """Filter wheel can be controlled from the same Controller. If
            so, then we will load this as a shared device. If not, we will create the
            connection to the Controller.

            TODO: Evaluate whether MS2000 should be able to operate as a shared device.
            """

            from navigate.model.devices.stages.asi_MSTwoThousand import (
                build_ASI_Stage_connection,
            )
            from navigate.model.devices.APIs.asi.asi_MS2000_controller import (
                MS2000Exception,
            )

            stage_devices.append(
                SerialConnectionFactory.build_connection(
                    build_ASI_Stage_connection,
                    (
                        stage_config["port"],
                        stage_config["baudrate"],
                    ),
                    exception=MS2000Exception,
                )
            )

        elif stage_type == "MFC2000" and platform.system() == "Windows":
            """Filter wheel can be controlled from the same Tiger Controller. If
            so, then we will load this as a shared device. If not, we will create the
            connection to the Tiger Controller.

            TODO: Evaluate whether MFC2000 should be able to operate as a shared device.
            """
            from navigate.model.devices.stages.asi_MFCTwoThousand import (
                build_ASI_Stage_connection,
            )
            from navigate.model.devices.APIs.asi.asi_tiger_controller import (
                TigerException,
            )

            stage_devices.append(
                SerialConnectionFactory.build_connection(
                    build_ASI_Stage_connection,
                    (
                        stage_config["port"],
                        stage_config["baudrate"],
                    ),
                    exception=TigerException,
                )
            )

        elif stage_type == "GalvoNIStage" and platform.system() == "Windows":
            stage_devices.append(DummyDeviceConnection())

        elif (
            stage_type.lower() == "syntheticstage" or stage_type.lower() == "synthetic"
        ):
            stage_devices.append(DummyDeviceConnection())

        elif "stage" in plugin_devices:
            is_found = False
            for load_function in plugin_devices["stage"]["load_device"]:
                try:
                    device_connection = load_function(
                        stage_config, is_synthetic, device_type="stage"
                    )
                    stage_devices.append(device_connection)
                    is_found = True
                    break
                except RuntimeError:
                    continue
            if not is_found:
                device_not_found(stage_type)

        else:
            device_not_found(stage_type)

    return stage_devices


def start_stage(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    id: int = 0,
    is_synthetic: bool = False,
    plugin_devices: Optional[Dict] = None,
) -> StageBase:
    """Initialize the Stage class.

    Proper stage types include PI, MP285, Thorlabs, MCL, ASI, GalvoNIStage,
    and SyntheticStage.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    id : int
        ID of the stage. Default is 0.
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[Dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Stage : StageBase
        An instance of the appropriate stage class depending on the device
        configuration.
    """
    if plugin_devices is None:
        plugin_devices = {}

    device_config = configuration["configuration"]["microscopes"][microscope_name][
        "stage"
    ]["hardware"]
    if is_synthetic:
        device_type = "SyntheticStage"

    elif type(device_config) == ListProxy:
        device_type = device_config[id]["type"]

    else:
        device_type = device_config["type"]

    if device_type == "PI":
        from navigate.model.devices.stages.pi import PIStage

        return PIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "MP285":
        from navigate.model.devices.stages.sutter import SutterStage

        return SutterStage(microscope_name, device_connection, configuration, id)

    elif device_type == "Thorlabs":
        from navigate.model.devices.stages.tl_kcube_inertial import TLKIMStage

        return TLKIMStage(microscope_name, device_connection, configuration, id)

    elif device_type == "KST101":
        from navigate.model.devices.stages.tl_kcube_steppermotor import TLKSTStage

        return TLKSTStage(microscope_name, device_connection, configuration, id)

    elif device_type == "MCL":
        from navigate.model.devices.stages.mcl import MCLStage

        return MCLStage(microscope_name, device_connection, configuration, id)

    elif device_type == "ASI":
        from navigate.model.devices.stages.asi import ASIStage

        return ASIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "MS2000":
        from navigate.model.devices.stages.asi_MSTwoThousand import ASIStage

        return ASIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "MFC2000":
        from navigate.model.devices.stages.asi import ASIStage

        return ASIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "GalvoNIStage":
        from navigate.model.devices.stages.ni import GalvoNIStage

        return GalvoNIStage(microscope_name, device_connection, configuration, id)

    elif device_type.lower() == "syntheticstage" or device_type.lower() == "synthetic":
        from navigate.model.devices.stages.synthetic import SyntheticStage

        return SyntheticStage(microscope_name, device_connection, configuration, id)

    elif "stage" in plugin_devices:
        for start_function in plugin_devices["stage"]["start_device"]:
            try:
                return start_function(
                    microscope_name,
                    device_connection,
                    configuration,
                    is_synthetic,
                    device_type="stage",
                    id=id,
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "stage", device_type, id)

    else:
        device_not_found(microscope_name, "stage", device_type, id)


def load_zoom_connection(
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: Optional[Dict] = None,
) -> Any:
    """Initializes the Zoom class on a dedicated thread.

    Load zoom information from the configuration file. Proper zoom types include
    DynamixelZoom and SyntheticZoom.

    Parameters
    ----------
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : Optional[Dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Zoom : Any
        Zoom class.
    """

    if plugin_devices is None:
        plugin_devices = {}

    device_info = configuration["configuration"]["hardware"]["zoom"]
    if is_synthetic:
        device_type = "SyntheticZoom"

    else:
        device_type = device_info["type"]

    if device_type == "DynamixelZoom":
        from navigate.model.devices.zoom.dynamixel import (
            build_dynamixel_zoom_connection,
        )

        return auto_redial(
            build_dynamixel_zoom_connection, (configuration,), exception=Exception
        )

    elif device_type.lower() == "syntheticzoom" or device_type.lower() == "synthetic":
        return DummyDeviceConnection()

    elif "zoom" in plugin_devices:
        for load_function in plugin_devices["zoom"]["load_device"]:
            try:
                return load_function(device_info, is_synthetic, device_type="zoom")
            except RuntimeError:
                continue
        device_not_found("Zoom", device_type)

    else:
        device_not_found("Zoom", device_type)


def start_zoom(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: Optional[dict] = None,
) -> ZoomBase:
    """Initializes the zoom class on a dedicated thread.

    Initializes the zoom: DynamixelZoom and SyntheticZoom.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Zoom : ZoomBase
        Zoom class.
    """
    if plugin_devices is None:
        plugin_devices = {}

    if is_synthetic:
        device_type = "SyntheticZoom"

    elif (
        "hardware"
        in configuration["configuration"]["microscopes"][microscope_name]["zoom"]
    ):
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "zoom"
        ]["hardware"]["type"]

    else:
        device_type = "NoDevice"

    if device_type == "DynamixelZoom":
        from navigate.model.devices.zoom.dynamixel import DynamixelZoom

        return DynamixelZoom(microscope_name, device_connection, configuration)

    elif device_type.lower() == "syntheticzoom" or device_type.lower() == "synthetic":
        from navigate.model.devices.zoom.synthetic import SyntheticZoom

        return SyntheticZoom(microscope_name, device_connection, configuration)

    elif device_type == "NoDevice" or "None":
        from navigate.model.devices.zoom.base import ZoomBase

        return ZoomBase(microscope_name, device_connection, configuration)

    elif "zoom" in plugin_devices:
        for start_zoom in plugin_devices["zoom"]["start_device"]:
            try:
                return start_zoom(
                    microscope_name,
                    device_connection,
                    configuration,
                    is_synthetic,
                    device_type="zoom",
                )
            except RuntimeError:
                continue
        device_not_found("Zoom", device_type)

    else:
        device_not_found("Zoom", device_type)


def load_filter_wheel_connection(
    device_info: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: Optional[dict] = None,
) -> Any:
    """Initializes the Filter Wheel class on a dedicated thread.

    Load filter wheel information from the configuration file. Proper filter wheel types
    include SutterFilterWheel, ASI, and SyntheticFilterWheel.

    Parameters
    ----------
    device_info : Dict[str, Any]
        filter wheel device configuration
    is_synthetic : bool
        Run synthetic version of hardware, Default is False.
    plugin_devices : Optional[dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Filter : Any
        Filter class.
    """
    if plugin_devices is None:
        plugin_devices = {}

    if is_synthetic:
        device_type = "SyntheticFilterWheel"

    else:
        device_type = device_info["type"]

    if device_type == "SutterFilterWheel":
        from navigate.model.devices.filter_wheel.sutter import (
            build_filter_wheel_connection,
        )

        return SerialConnectionFactory.build_connection(
            build_filter_wheel_connection,
            (device_info["port"], device_info["baudrate"], 0.25),
            exception=Exception,
        )

    elif device_type == "LUDLFilterWheel":
        from navigate.model.devices.filter_wheel.ludl import (
            build_filter_wheel_connection,
        )

        return SerialConnectionFactory.build_connection(
            build_filter_wheel_connection,
            (device_info["port"], device_info["baudrate"], 0.25),
            exception=Exception,
        )

    elif device_type == "ASI" or device_type == "ASICubeSlider":
        from navigate.model.devices.filter_wheel.asi import (
            build_filter_wheel_connection,
        )

        return SerialConnectionFactory.build_connection(
            build_filter_wheel_connection,
            (device_info["port"], device_info["baudrate"], 0.25),
            exception=Exception,
        )

    elif device_type == "NI":
        return DummyDeviceConnection()

    elif (
        device_type.lower() == "syntheticfilterwheel"
        or device_type.lower() == "synthetic"
    ):
        return DummyDeviceConnection()

    elif "filter_wheel" in plugin_devices:
        for load_function in plugin_devices["filter_wheel"]["load_device"]:
            try:
                return load_function(
                    device_info, is_synthetic, device_type="filter_wheel"
                )
            except RuntimeError:
                continue
        device_not_found("filter_wheel", device_type)

    else:
        device_not_found("filter_wheel", device_type)


def start_filter_wheel(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    id: int = 0,
    is_synthetic: bool = False,
    plugin_devices: Optional[dict] = None,
) -> FilterWheelBase:
    """Initialize the filter wheel class.

    Initializes the filter wheel: SutterFilterWheel, ASI, and SyntheticFilterWheel.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Device connection
    configuration : Dict[str, Any]
        Global configuration of the microscope
    id : int
        Index of filter_wheel in the configuration dictionary. Default is 0.
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices :  Optional[dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    FilterWheel : FilterWheelBase
        FilterWheel class.
    """
    if plugin_devices is None:
        plugin_devices = {}

    if device_connection is None:
        device_not_found(microscope_name, "filter_wheel")

    device_config = configuration["configuration"]["microscopes"][microscope_name][
        "filter_wheel"
    ][id]

    if is_synthetic:
        device_type = "SyntheticFilterWheel"

    else:
        device_type = device_config["hardware"]["type"]

    if device_type == "SutterFilterWheel":
        from navigate.model.devices.filter_wheel.sutter import SutterFilterWheel

        return SutterFilterWheel(device_connection, device_config)

    elif device_type == "LUDLFilterWheel":
        from navigate.model.devices.filter_wheel.ludl import LUDLFilterWheel

        return LUDLFilterWheel(device_connection, device_config)

    elif device_type == "ASI":
        from navigate.model.devices.filter_wheel.asi import ASIFilterWheel

        return ASIFilterWheel(device_connection, device_config)

    elif device_type == "ASICubeSlider":
        from navigate.model.devices.filter_wheel.asi import ASICubeSlider

        return ASICubeSlider(device_connection, device_config)

    elif device_type == "NI":
        from navigate.model.devices.filter_wheel.ni import DAQFilterWheel

        return DAQFilterWheel(device_connection, device_config)

    elif (
        device_type.lower() == "syntheticfilterwheel"
        or device_type.lower() == "synthetic"
    ):
        from navigate.model.devices.filter_wheel.synthetic import SyntheticFilterWheel

        return SyntheticFilterWheel(device_connection, device_config)

    elif "filter_wheel" in plugin_devices:
        for start_function in plugin_devices["filter_wheel"]["start_device"]:
            try:
                return start_function(
                    microscope_name,
                    device_connection,
                    configuration,
                    is_synthetic,
                    device_type="filter_wheel",
                    id=id,
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "filter_wheel", device_type)

    else:
        device_not_found(microscope_name, "filter_wheel", device_type)


def start_daq(configuration: Dict[str, Any], is_synthetic: bool = False) -> DAQBase:
    """Initializes the data acquisition (DAQ) class on a dedicated thread.

    Load daq information from the configuration file. Proper daq types include NI and
    SyntheticDAQ.

    Parameters
    ----------
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.

    Returns
    -------
    DAQ : DAQBase
        DAQ class.
    """
    if is_synthetic:
        device_type = "SyntheticDAQ"

    else:
        device_type = configuration["configuration"]["hardware"]["daq"]["type"]

    if device_type == "NI":
        from navigate.model.devices.daq.ni import NIDAQ

        return NIDAQ(configuration)

    elif device_type.lower() == "syntheticdaq" or device_type.lower() == "synthetic":
        from navigate.model.devices.daq.synthetic import SyntheticDAQ

        return SyntheticDAQ(configuration)

    else:
        device_not_found(configuration["configuration"]["hardware"]["daq"]["type"])


def start_shutter(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: Optional[dict] = None,
) -> ShutterBase:
    """Initializes the shutter class on a dedicated thread.

    Initializes the shutters: Thorlabs, Shutter or SyntheticShutter
    Shutters are triggered via digital outputs on the NI DAQ Card
    Thus, requires both to be enabled.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Shutter : ShutterBase
        Shutter class.
    """

    if plugin_devices is None:
        plugin_devices = {}
    if is_synthetic:
        device_type = "SyntheticShutter"

    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "shutter"
        ]["hardware"]["type"]

    if device_type == "NI":
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.shutter.ni import ShutterTTL

        return ShutterTTL(microscope_name, None, configuration)

    elif (
        device_type.lower() == "syntheticshutter" or device_type.lower() == "synthetic"
    ):
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.shutter.synthetic import SyntheticShutter

        return SyntheticShutter(microscope_name, None, configuration)

    elif "shutter" in plugin_devices:
        for start_function in plugin_devices["shutter"]["start_device"]:
            try:
                return start_function(
                    microscope_name,
                    None,
                    configuration,
                    is_synthetic,
                    device_type="shutter",
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "shutter", device_type)

    else:
        device_not_found(microscope_name, "shutter", device_type)


def start_lasers(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    id: int = 0,
    is_synthetic: bool = False,
    plugin_devices: Optional[dict] = None,
) -> LaserBase:
    """Initializes the lasers.

    Loads the lasers from the configuration file. Proper laser types include NI and
    SyntheticLaser. Initializes the Laser Switching, Analog, and Digital DAQ Outputs.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    id : int
        Index of laser in laser list in configuration dictionary. Default is 0.
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    laser : LaserBase
        Laser class.
    """

    if plugin_devices is None:
        plugin_devices = {}

    if is_synthetic:
        device_type = "SyntheticLaser"

    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "lasers"
        ][id]["power"]["hardware"]["type"]

    if device_type == "NI":
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.lasers.ni import LaserNI

        return LaserNI(microscope_name, device_connection, configuration, id)

    elif device_type.lower() == "syntheticlaser" or device_type.lower() == "synthetic":
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.lasers.synthetic import SyntheticLaser

        return SyntheticLaser(microscope_name, device_connection, configuration, id)

    elif "lasers" in plugin_devices:
        for start_function in plugin_devices["lasers"]["start_device"]:
            try:
                return start_function(
                    microscope_name,
                    device_connection,
                    configuration,
                    is_synthetic,
                    device_type="lasers",
                    id=id,
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "laser", device_type, id)

    else:
        device_not_found(microscope_name, "laser", device_type, id)


def start_remote_focus_device(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    is_synthetic: bool = False,
    plugin_devices: Optional[dict] = None,
) -> RemoteFocusBase:
    """Initializes the remote focus class.

    Initializes the Remote Focusing Device. Proper remote focus types include
    NI, EquipmentSolutions, and SyntheticRemoteFocus.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    remote_focus : RemoteFocusBase
        Remote focusing class.
    """

    if plugin_devices is None:
        plugin_devices = {}

    if is_synthetic:
        device_type = "SyntheticRemoteFocus"

    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "remote_focus_device"
        ]["hardware"]["type"]

    if device_type == "NI":
        from navigate.model.devices.remote_focus.ni import RemoteFocusNI

        return RemoteFocusNI(microscope_name, device_connection, configuration)

    elif device_type == "EquipmentSolutions":
        from navigate.model.devices.remote_focus.equipment_solutions import (
            RemoteFocusEquipmentSolutions,
        )

        return RemoteFocusEquipmentSolutions(
            microscope_name, device_connection, configuration
        )

    elif (
        device_type.lower() == "syntheticremotefocus"
        or device_type.lower() == "synthetic"
    ):
        from navigate.model.devices.remote_focus.synthetic import (
            SyntheticRemoteFocus,
        )

        return SyntheticRemoteFocus(microscope_name, device_connection, configuration)

    elif "remote_focus_device" in plugin_devices:
        for start_function in plugin_devices["remote_focus_device"]["start_device"]:
            try:
                return start_function(
                    microscope_name,
                    device_connection,
                    configuration,
                    is_synthetic,
                    device_type="remote_focus_device",
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "remote_focus", device_type)

    else:
        device_not_found(microscope_name, "remote_focus", device_type)


def start_galvo(
    microscope_name: str,
    device_connection: Any,
    configuration: Dict[str, Any],
    id: int = 0,
    is_synthetic: bool = False,
    plugin_devices: Optional[dict] = None,
) -> GalvoBase:
    """Initializes the Galvo class.

    Initializes the Galvo Device. Proper galvo types include NI and SyntheticGalvo.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : Any
        Hardware device to connect to
    configuration : Dict[str, Any]
        Global configuration of the microscope
    id : int
        Index of galvo in the configuration dictionary. Default is 0.
    is_synthetic : bool
        Run synthetic version of hardware. Default is False.
    plugin_devices : Optional[dict]
        Dictionary of plugin devices. Default is None.

    Returns
    -------
    Galvo : GalvoBase
        Galvo scanning class.
    """

    if plugin_devices is None:
        plugin_devices = {}

    if is_synthetic:
        device_type = "SyntheticGalvo"

    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "galvo"
        ][id]["hardware"]["type"]

    if device_type == "NI":
        from navigate.model.devices.galvo.ni import GalvoNI

        return GalvoNI(microscope_name, device_connection, configuration, id)

    elif device_type.lower() == "syntheticgalvo" or device_type.lower() == "synthetic":
        from navigate.model.devices.galvo.synthetic import SyntheticGalvo

        return SyntheticGalvo(microscope_name, device_connection, configuration, id)

    elif "galvo" in plugin_devices:
        for start_function in plugin_devices["galvo"]["start_device"]:
            try:
                return start_function(
                    microscope_name,
                    device_connection,
                    configuration,
                    is_synthetic,
                    device_type="galvo",
                    id=id,
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "galvo", id, device_type)

    else:
        device_not_found(microscope_name, "galvo", id, device_type)


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
    configuration: Dict[str, Any], is_synthetic=False, plugin_devices=None
) -> dict:
    """Load devices from configuration.

    Parameters
    ----------
    configuration : Dict[str, Any]
        Configuration dictionary
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    devices : dict
        Dictionary of devices
    """

    if plugin_devices is None:
        plugin_devices = {}

    devices = {}
    # load camera
    if "camera" in configuration["configuration"]["hardware"].keys():
        devices["camera"] = {}
        for id, device in enumerate(
            configuration["configuration"]["hardware"]["camera"]
        ):
            try:
                camera = load_camera_connection(configuration, id, is_synthetic)
            except RuntimeError as e:  # noqa
                if "camera" in plugin_devices:
                    camera = plugin_devices["camera"]["load_device"](
                        configuration, id, is_synthetic
                    )
                else:
                    error_statement = f"Error loading camera: {e}"
                    logger.error(error_statement)
                    raise Exception(error_statement)

            if (not is_synthetic) and device["type"].startswith("Hamamatsu"):
                camera_serial_number = str(camera._serial_number)
                device_ref_name = camera_serial_number
                # if the serial number has leading zeros,
                # the yaml reader will convert it to an octal number
                if camera_serial_number.startswith("0"):
                    try:
                        oct_num = int(camera_serial_number, 8)
                        device_ref_name = str(oct_num)
                    except ValueError:
                        logger.debug("Error converting camera serial number to octal")
                        pass
            else:
                device_ref_name = str(device["serial_number"])
            devices["camera"][device_ref_name] = camera

    # load mirror
    if "mirror" in configuration["configuration"]["hardware"].keys():
        devices["mirror"] = {}
        device = configuration["configuration"]["hardware"]["mirror"]
        device_ref_name = build_ref_name("_", device["type"])
        devices["mirror"][device_ref_name] = load_mirror(configuration, is_synthetic)

    # load zoom
    if "zoom" in configuration["configuration"]["hardware"].keys():
        devices["zoom"] = {}
        device = configuration["configuration"]["hardware"]["zoom"]
        device_ref_name = build_ref_name("_", device["type"], device["servo_id"])
        devices["zoom"][device_ref_name] = load_zoom_connection(
            configuration, is_synthetic, plugin_devices
        )

    # load daq
    if "daq" in configuration["configuration"]["hardware"].keys():
        devices["daq"] = start_daq(configuration, is_synthetic)

    # load filter wheels
    if "filter_wheel" in configuration["configuration"]["hardware"].keys():
        devices["filter_wheel"] = {}
        filter_wheels = configuration["configuration"]["hardware"]["filter_wheel"]
        for i, filter_wheel_config in enumerate(filter_wheels):
            device_ref_name = build_ref_name(
                "_", filter_wheel_config["type"], filter_wheel_config["wheel_number"]
            )
            devices["filter_wheel"][device_ref_name] = load_filter_wheel_connection(
                filter_wheel_config, is_synthetic, plugin_devices
            )

    # load stage
    if "stage" in configuration["configuration"]["hardware"].keys():
        device_config = configuration["configuration"]["hardware"]["stage"]
        devices["stages"] = {}
        stages = load_stages(configuration, is_synthetic, plugin_devices)
        for i, stage in enumerate(stages):
            device_ref_name = build_ref_name(
                "_", device_config[i]["type"], device_config[i]["serial_number"]
            )
            devices["stages"][device_ref_name] = stage

    return devices
