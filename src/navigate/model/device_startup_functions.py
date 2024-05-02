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


# Standard Library Imports
import platform
import logging
import time
import importlib
from multiprocessing.managers import ListProxy

# Third Party Imports

# Local Imports
from navigate.tools.common_functions import build_ref_name

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class DummyDeviceConnection:
    """Dummy Device"""

    pass


def auto_redial(func, args, n_tries=10, exception=Exception, **kwargs):
    """Retries connections to a startup device defined by func n_tries times.

    Parameters
    ----------
    func : function or class
        The function or class (__init__() function) that connects to a device.
    args : tuple
        Arguments to function or class
    n_tries : int
        The number of tries to redial.
    exception : inherits from BaseException
        An exception type to check on each connection attempt.

    Returns
    -------
    val : object
        Result of func

    Examples
    --------
    >>> auto_redial(DCAM, (0,), exception=Exception)

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
                raise exception
        else:
            break

    return val


def load_camera_connection(configuration, camera_id=0, is_synthetic=False):
    """Initializes the camera api class.

    Load camera information from the configuration file. Proper camera types include
    HamamatsuOrca, HamamatsuOrcaLightning, Photometrics, and SyntheticCamera.

    Parameters
    ----------
    configuration : multiprocessing.managers.DictProxy
        Global configuration of the microscope
    camera_id : int
        Device ID (0, 1...)
    is_synthetic: bool
        Whether it is a synthetic hardware

    Returns
    -------
    Camera controller: class
        Camera api class.

    Examples
    --------
    >>> load_camera_connection(configuration, camera_id=0, is_synthetic=False)
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
        from navigate.model.devices.camera.camera_synthetic import (
            SyntheticCameraController,
        )

        return SyntheticCameraController()

    elif cam_type == "Photometrics":
        from navigate.model.devices.camera.camera_photometrics import (
            build_photometrics_connection,
        )

        camera_connection = configuration["configuration"]["hardware"]["camera"][
            camera_id
        ]["camera_connection"]

        # return camera object in the auto_redial function.
        return auto_redial(
            build_photometrics_connection, (camera_connection,), exception=Exception
        )
    else:
        device_not_found("camera", camera_id, cam_type)


def start_camera(
    microscope_name,
    device_connection,
    configuration,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the camera class.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocessing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Camera : class
        Camera class.

    Examples
    --------
    >>> start_camera(microscope_name, device_connection, configuration,
        is_synthetic=False)
    """
    if device_connection is None:
        device_not_found(microscope_name, "camera")

    if is_synthetic:
        cam_type = "SyntheticCamera"
    else:
        cam_type = configuration["configuration"]["microscopes"][microscope_name][
            "camera"
        ]["hardware"]["type"]

    if cam_type == "HamamatsuOrca":
        from navigate.model.devices.camera.camera_hamamatsu import HamamatsuOrca

        return HamamatsuOrca(microscope_name, device_connection, configuration)

    elif cam_type == "HamamatsuOrcaLightning":
        from navigate.model.devices.camera.camera_hamamatsu import (
            HamamatsuOrcaLightning,
        )

        return HamamatsuOrcaLightning(microscope_name, device_connection, configuration)

    elif cam_type == "HamamatsuOrcaFire":
        from navigate.model.devices.camera.camera_hamamatsu import (
            HamamatsuOrcaFire,
        )

        return HamamatsuOrcaFire(microscope_name, device_connection, configuration)

    elif cam_type == "HamamatsuOrcaFusion":
        from navigate.model.devices.camera.camera_hamamatsu import (
            HamamatsuOrcaFusion,
        )

        return HamamatsuOrcaFusion(microscope_name, device_connection, configuration)

    elif cam_type == "Photometrics":
        from navigate.model.devices.camera.camera_photometrics import (
            PhotometricsBase,
        )

        return PhotometricsBase(microscope_name, device_connection, configuration)

    elif cam_type.lower() == "syntheticcamera" or cam_type.lower() == "synthetic":
        from navigate.model.devices.camera.camera_synthetic import SyntheticCamera

        return SyntheticCamera(microscope_name, device_connection, configuration)

    elif "camera" in plugin_devices:

        for start_function in plugin_devices["camera"]["start_device"]:
            try:
                return start_function(
                    microscope_name, device_connection, configuration, is_synthetic,
                    device_type="camera"
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "camera", cam_type)
    else:
        device_not_found(microscope_name, "camera", cam_type)


def load_mirror(configuration, is_synthetic=False):
    """Initializes the deformable mirror class on a dedicated thread.

    Parameters
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?

    Returns
    -------
    Mirror : class
        Mirror class.
    """
    if is_synthetic:
        mirror_type = "SyntheticMirror"
    else:
        mirror_type = configuration["configuration"]["hardware"]["mirror"][
            "type"
        ]  # only one mirror for now...

    if mirror_type == "ImagineOpticsMirror":
        from navigate.model.devices.APIs.imagineoptics.imop import IMOP_Mirror

        return auto_redial(IMOP_Mirror, (), exception=Exception)
    elif mirror_type == "SyntheticMirror":
        return DummyDeviceConnection()
    else:
        device_not_found("mirror", mirror_type)


def start_mirror(
    microscope_name,
    device_connection,
    configuration,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the mirror class.

    Parameters
    ----------
    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Mirror : class
        Mirror class.
    """
    if device_connection is None or is_synthetic:
        mirror_type = "SyntheticMirror"
    else:
        mirror_type = configuration["configuration"]["microscopes"][microscope_name][
            "mirror"
        ]["hardware"]["type"]

    if mirror_type == "ImagineOpticsMirror":
        from navigate.model.devices.mirrors.mirror_imop import ImagineOpticsMirror

        return ImagineOpticsMirror(microscope_name, device_connection, configuration)
    elif mirror_type == "SyntheticMirror":
        from navigate.model.devices.mirrors.mirror_synthetic import SyntheticMirror

        return SyntheticMirror(microscope_name, device_connection, configuration)
    elif "mirror" in plugin_devices:
        return plugin_devices["mirror"]["start_device"](
            microscope_name, device_connection, configuration
        )
    else:
        device_not_found(microscope_name, "mirror", mirror_type)


def load_stages(configuration, is_synthetic=False, plugin_devices={}):
    """Initializes the stage class on a dedicated thread.

    Stage information is pulled from the configuration file. Proper stage types include
    PI, MP285, Thorlabs, MCL, ASI, GalvoNIStage, and SyntheticStage.

    Parameters
    ----------
    configuration : multiprocessing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Stage : class
        Stage class.

    Examples
    --------
    >>> load_stages(configuration, is_synthetic=False, plugin_devices={})
    """
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
            from navigate.model.devices.stages.stage_pi import build_PIStage_connection
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
            from navigate.model.devices.stages.stage_sutter import (
                build_MP285_connection,
            )

            stage_devices.append(
                auto_redial(
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
            from navigate.model.devices.stages.stage_tl_kcube_inertial import (
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

        elif stage_type == "MCL" and platform.system() == "Windows":
            from navigate.model.devices.stages.stage_mcl import (
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
            filter_wheel = configuration["configuration"]["hardware"]["filter_wheel"][
                "type"
            ]
            if filter_wheel == "ASI":
                stage_devices.append("shared device")
            else:
                from navigate.model.devices.stages.stage_asi import (
                    build_ASI_Stage_connection,
                )
                from navigate.model.devices.APIs.asi.asi_tiger_controller import (
                    TigerException,
                )

                stage_devices.append(
                    auto_redial(
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
            filter_wheel = configuration["configuration"]["hardware"]["filter_wheel"][
                "type"
            ]

            if filter_wheel == "MS2000":
                stage_devices.append("shared device")
            else:
                from navigate.model.devices.stages.stage_asi_MSTwoThousand import (
                    build_ASI_Stage_connection,
                )
                from navigate.model.devices.APIs.asi.asi_MS2000_controller import (
                    MS2000Exception,
                )

                stage_devices.append(
                    auto_redial(
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
            filter_wheel = configuration["configuration"]["hardware"]["filter_wheel"][
                "type"
            ]
            if filter_wheel == "MFC2000":
                stage_devices.append("shared device")
            else:
                from navigate.model.devices.stages.stage_asi_MFCTwoThousand import (
                    build_ASI_Stage_connection,
                )
                from navigate.model.devices.APIs.asi.asi_tiger_controller import (
                    TigerException,
                )

                stage_devices.append(
                    auto_redial(
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
    microscope_name,
    device_connection,
    configuration,
    id=0,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the Stage class. Proper stage types include PI, MP285, Thorlabs, MCL,
    ASI, GalvoNIStage, and SyntheticStage.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    id : int
        ID of the stage
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Stage : class
        Stage class.

    Examples
    --------
    >>> start_stage(microscope_name, device_connection, configuration, id=0,
                    is_synthetic=False)
    """
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
        from navigate.model.devices.stages.stage_pi import PIStage

        return PIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "MP285":
        from navigate.model.devices.stages.stage_sutter import SutterStage

        return SutterStage(microscope_name, device_connection, configuration, id)

    elif device_type == "Thorlabs":
        from navigate.model.devices.stages.stage_tl_kcube_inertial import TLKIMStage

        return TLKIMStage(microscope_name, device_connection, configuration, id)
    
    elif device_type == "KST101":
        from navigate.model.devices.stages.stage_tl_kcube_steppermotor import TLKSTStage

        return TLKSTStage(microscope_name, device_connection, configuration, id)
    
    elif device_type == "MCL":
        from navigate.model.devices.stages.stage_mcl import MCLStage

        return MCLStage(microscope_name, device_connection, configuration, id)

    elif device_type == "ASI":
        from navigate.model.devices.stages.stage_asi import ASIStage

        return ASIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "MS2000":
        from navigate.model.devices.stages.stage_asi_MSTwoThousand import ASIStage

        return ASIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "MFC2000":
        from navigate.model.devices.stages.stage_asi import ASIStage

        return ASIStage(microscope_name, device_connection, configuration, id)

    elif device_type == "GalvoNIStage":
        from navigate.model.devices.stages.stage_galvo import GalvoNIStage

        return GalvoNIStage(microscope_name, device_connection, configuration, id)

    elif device_type.lower() == "syntheticstage" or device_type.lower() == "synthetic":
        from navigate.model.devices.stages.stage_synthetic import SyntheticStage

        return SyntheticStage(microscope_name, device_connection, configuration, id)

    elif "stage" in plugin_devices:

        for start_function in plugin_devices["stage"]["start_device"]:
            try:
                return start_function(
                    microscope_name, device_connection, configuration, is_synthetic,
                    device_type="stage", id=id
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "stage", device_type, id)
    else:
        device_not_found(microscope_name, "stage", device_type, id)


def load_zoom_connection(configuration, is_synthetic=False, plugin_devices={}):
    """Initializes the Zoom class on a dedicated thread.

    Load zoom information from the configuration file. Proper zoom types include
    DynamixelZoom and SyntheticZoom.

    Parameters
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Zoom : class
        Zoom class.

    Examples
    --------
    >>> load_zoom_connection(configuration, is_synthetic=False)
    """

    device_info = configuration["configuration"]["hardware"]["zoom"]
    if is_synthetic:
        device_type = "SyntheticZoom"
    else:
        device_type = device_info["type"]

    if device_type == "DynamixelZoom":
        from navigate.model.devices.zoom.zoom_dynamixel import (
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
    microscope_name,
    device_connection,
    configuration,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the zoom class on a dedicated thread.

    Initializes the zoom: DynamixelZoom and SyntheticZoom.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Zoom : class
        Zoom class.

    Examples
    --------
    >>> start_zoom(microscope_name, device_connection, configuration,
                   is_synthetic=False)
    """
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
        from navigate.model.devices.zoom.zoom_dynamixel import DynamixelZoom

        return DynamixelZoom(microscope_name, device_connection, configuration)
    elif device_type.lower() == "syntheticzoom" or device_type.lower() == "synthetic":
        from navigate.model.devices.zoom.zoom_synthetic import SyntheticZoom

        return SyntheticZoom(microscope_name, device_connection, configuration)
    elif device_type == "NoDevice" or "None":
        from navigate.model.devices.zoom.zoom_base import ZoomBase

        return ZoomBase(microscope_name, device_connection, configuration)
    elif "zoom" in plugin_devices:

        for start_zoom in plugin_devices["zoom"]["start_device"]:
            try:
                return start_zoom(
                    microscope_name, device_connection, configuration, is_synthetic,
                    device_type="zoom"
                )
            except RuntimeError:
                continue
        device_not_found("Zoom", device_type)
    else:
        device_not_found("Zoom", device_type)


def load_filter_wheel_connection(configuration, is_synthetic=False, plugin_devices={}):
    """Initializes the Filter Wheel class on a dedicated thread.

    Load filter wheel information from the configuration file. Proper filter wheel types
    include SutterFilterWheel, ASI, and SyntheticFilterWheel.

    Parameters
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Filter : class
        Filter class.
    """
    device_info = configuration["configuration"]["hardware"]["filter_wheel"]
    if is_synthetic:
        device_type = "SyntheticFilterWheel"

    else:
        device_type = device_info["type"]

    if device_type == "SutterFilterWheel":
        from navigate.model.devices.filter_wheel.filter_wheel_sutter import (
            build_filter_wheel_connection,
        )

        return auto_redial(
            build_filter_wheel_connection,
            (device_info["port"], device_info["baudrate"], 0.25),
            exception=Exception,
        )

    elif device_type == "ASI":
        from navigate.model.devices.filter_wheel.filter_wheel_asi import (
            build_filter_wheel_connection,
        )

        tiger_controller = auto_redial(
            build_filter_wheel_connection,
            (device_info["port"], device_info["baudrate"], 0.25),
            exception=Exception,
        )
        return tiger_controller

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
    microscope_name,
    device_connection,
    configuration,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the filter wheel class on a dedicated thread.

    Initializes the filter wheel: SutterFilterWheel, ASI, and SyntheticFilterWheel.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    FilterWheel : class
        FilterWheel class.

    Examples
    --------
    >>> start_filter_wheel(microscope_name, device_connection, configuration,
                           is_synthetic=False)

    """
    if device_connection is None:
        device_not_found(microscope_name, "filter_wheel")

    if is_synthetic:
        device_type = "SyntheticFilterWheel"
    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "filter_wheel"
        ]["hardware"]["type"]

    if device_type == "SutterFilterWheel":
        from navigate.model.devices.filter_wheel.filter_wheel_sutter import (
            SutterFilterWheel,
        )

        return SutterFilterWheel(microscope_name, device_connection, configuration)

    elif device_type == "ASI":
        from navigate.model.devices.filter_wheel.filter_wheel_asi import ASIFilterWheel

        return ASIFilterWheel(microscope_name, device_connection, configuration)

    elif (
        device_type.lower() == "syntheticfilterwheel"
        or device_type.lower() == "synthetic"
    ):
        from navigate.model.devices.filter_wheel.filter_wheel_synthetic import (
            SyntheticFilterWheel,
        )

        return SyntheticFilterWheel(microscope_name, device_connection, configuration)

    elif "filter_wheel" in plugin_devices:

        for start_function in plugin_devices["filter_wheel"]["start_device"]:
            try:
                return start_function(
                    microscope_name, device_connection, configuration, is_synthetic,
                    device_type="filter_wheel"
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "filter_wheel", device_type)
    else:
        device_not_found(microscope_name, "filter_wheel", device_type)


def start_daq(configuration, is_synthetic=False):
    """Initializes the data acquisition (DAQ) class on a dedicated thread.

    Load daq information from the configuration file. Proper daq types include NI and
    SyntheticDAQ.

    Parameters
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?

    Returns
    -------
    DAQ : class
        DAQ class.

    Examples
    --------
    >>> start_daq(configuration, is_synthetic=False)
    """
    if is_synthetic:
        device_type = "SyntheticDAQ"

    else:
        device_type = configuration["configuration"]["hardware"]["daq"]["type"]

    if device_type == "NI":
        from navigate.model.devices.daq.daq_ni import NIDAQ

        return NIDAQ(configuration)

    elif device_type.lower() == "syntheticdaq" or device_type.lower() == "synthetic":
        from navigate.model.devices.daq.daq_synthetic import SyntheticDAQ

        return SyntheticDAQ(configuration)

    else:
        device_not_found(configuration["configuration"]["hardware"]["daq"]["type"])


def start_shutter(
    microscope_name,
    device_connection,
    configuration,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the shutter class on a dedicated thread.

    Initializes the shutters: ThorlabsShutter or SyntheticShutter
    Shutters are triggered via digital outputs on the NI DAQ Card
    Thus, requires both to be enabled.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Shutter : class
        Shutter class.

    Examples
    --------
    >>> start_shutter(microscope_name, device_connection, configuration,
                      is_synthetic=False)
    """

    if is_synthetic:
        device_type = "SyntheticShutter"
    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "shutter"
        ]["hardware"]["type"]

    if device_type == "NI":
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.shutter.laser_shutter_ttl import ShutterTTL

        return ShutterTTL(microscope_name, None, configuration)
    elif (
        device_type.lower() == "syntheticshutter" or device_type.lower() == "synthetic"
    ):
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.shutter.laser_shutter_synthetic import (
            SyntheticShutter,
        )

        return SyntheticShutter(microscope_name, None, configuration)

    elif "shutter" in plugin_devices:

        for start_function in plugin_devices["shutter"]["start_device"]:
            try:
                return start_function(
                    microscope_name, None, configuration, is_synthetic,
                    device_type="shutter"
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "shutter", device_type)

    else:
        device_not_found(microscope_name, "shutter", device_type)


def start_lasers(
    microscope_name,
    device_connection,
    configuration,
    id=0,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the lasers.

    Loads the lasers from the configuration file. Proper laser types include NI and
    SyntheticLaser. Initializes the Laser Switching, Analog, and Digital DAQ Outputs.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    id : int
        Index of laser in laser list in configuration dictionary
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Triggers : class
        Trigger class.

    Examples
    --------
    >>> start_lasers(microscope_name, device_connection, configuration, id=0,
                     is_synthetic=False)
    """

    if is_synthetic:
        device_type = "SyntheticLaser"
    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "lasers"
        ][id]["power"]["hardware"]["type"]

    if device_type == "NI":
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.lasers.laser_ni import LaserNI

        return LaserNI(microscope_name, device_connection, configuration, id)
    elif device_type.lower() == "syntheticlaser" or device_type.lower() == "synthetic":
        if device_connection is not None:
            return device_connection
        from navigate.model.devices.lasers.laser_synthetic import SyntheticLaser

        return SyntheticLaser(microscope_name, device_connection, configuration, id)
    elif "lasers" in plugin_devices:
        for start_function in plugin_devices["lasers"]["start_device"]:
            try:
                return start_function(
                    microscope_name, device_connection, configuration, is_synthetic, device_type="lasers", id=id
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "laser", device_type, id)
    else:
        device_not_found(microscope_name, "laser", device_type, id)


def start_remote_focus_device(
    microscope_name,
    device_connection,
    configuration,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the remote focus class.

    Initializes the Remote Focusing Device. Proper remote focus types include
    NI, EquipmentSolutions, and SyntheticRemoteFocus.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Remote Focus : class
        Remote focusing class.

    Examples
    --------
    >>> start_remote_focus_device(microscope_name, device_connection, configuration,
                                  is_synthetic=False)
    """

    if is_synthetic:
        device_type = "SyntheticRemoteFocus"
    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "remote_focus_device"
        ]["hardware"]["type"]

    if device_type == "NI":
        from navigate.model.devices.remote_focus.remote_focus_ni import RemoteFocusNI

        return RemoteFocusNI(microscope_name, device_connection, configuration)

    elif device_type == "EquipmentSolutions":
        from navigate.model.devices.remote_focus.remote_focus_equipment_solutions import (
            RemoteFocusEquipmentSolutions,
        )

        return RemoteFocusEquipmentSolutions(
            microscope_name, device_connection, configuration
        )

    elif (
        device_type.lower() == "syntheticremotefocus"
        or device_type.lower() == "synthetic"
    ):
        from navigate.model.devices.remote_focus.remote_focus_synthetic import (
            SyntheticRemoteFocus,
        )

        return SyntheticRemoteFocus(microscope_name, device_connection, configuration)

    elif "remote_focus_device" in plugin_devices:

        for start_function in plugin_devices["remote_focus_device"]["start_device"]:
            try:
                return start_function(
                    microscope_name, device_connection, configuration, is_synthetic,
                    device_type="remote_focus_device"
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "remote_focus", device_type)

    else:
        device_not_found(microscope_name, "remote_focus", device_type)


def start_galvo(
    microscope_name,
    device_connection,
    configuration,
    id=0,
    is_synthetic=False,
    plugin_devices={},
):
    """Initializes the Galvo class.

    Initializes the Galvo Device. Proper galvo types include NI and SyntheticGalvo.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    id : int
        Index of galvo in the configuration dictionary
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    Galvo : class
        Galvo scanning class.

    Examples
    --------
    >>> start_galvo(microscope_name, device_connection, configuration, id=0,
                    is_synthetic=False)
    """

    if is_synthetic:
        device_type = "SyntheticGalvo"
    else:
        device_type = configuration["configuration"]["microscopes"][microscope_name][
            "galvo"
        ][id]["hardware"]["type"]

    if device_type == "NI":
        from navigate.model.devices.galvo.galvo_ni import GalvoNI

        return GalvoNI(microscope_name, device_connection, configuration, id)
    elif device_type.lower() == "syntheticgalvo" or device_type.lower() == "synthetic":
        from navigate.model.devices.galvo.galvo_synthetic import SyntheticGalvo

        return SyntheticGalvo(microscope_name, device_connection, configuration, id)
    elif "galvo" in plugin_devices:
        for start_function in plugin_devices["galvo"]["start_device"]:
            try:
                return start_function(
                    microscope_name, device_connection, configuration, is_synthetic,
                    device_type="galvo", id=id
                )
            except RuntimeError:
                continue
        device_not_found(microscope_name, "galvo", id, device_type)

    else:
        device_not_found(microscope_name, "galvo", id, device_type)


def device_not_found(*args):
    """Display error message if device not found.

    Raises error if the configuration is incorrect and/or the device is not found.

    Parameters
    ----------
    *args
        microscope_name
        device
        device id
        device type

    Returns
    -------
    devices : class
        Device class.

    Examples
    --------
    >>> device_not_found(microscope_name, "galvo", id, device_type)

    """
    print("Device Not Found in Configuration.YML:", args)
    raise RuntimeError(f"Device not found in configuration: {args}")


def load_devices(configuration, is_synthetic=False, plugin_devices={}) -> dict:
    """Load devices from configuration.

    Parameters
    ----------
    configuration
        Configuration dictionary
    is_synthetic : bool
        Run synthetic version of hardware?
    plugin_devices : dict
        Dictionary of plugin devices

    Returns
    -------
    devices : dict
        Dictionary of devices

    Examples
    --------
    >>> load_devices(configuration, is_synthetic=False)

    """

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

            if (not is_synthetic) and device["type"].startswith("Hamamatsu"):
                camera_serial_number = str(camera._serial_number)
                device_ref_name = build_ref_name(
                    "_", device["type"], camera_serial_number
                )
                # if the serial number has leading zeros,
                # the yaml reader will convert it to an octal number
                if camera_serial_number.startswith("0"):
                    try:
                        oct_num = int(camera_serial_number, 8)
                        devices["camera"][
                            build_ref_name("_", device["type"], oct_num)
                        ] = camera
                    except ValueError:
                        pass
            else:
                device_ref_name = build_ref_name(
                    "_", device["type"], device["serial_number"]
                )
            devices["camera"][device_ref_name] = camera

    # load mirror
    if "mirror" in configuration["configuration"]["hardware"].keys():
        devices["mirror"] = {}
        device = configuration["configuration"]["hardware"]["mirror"]
        device_ref_name = build_ref_name("_", device["type"])
        devices["mirror"][device_ref_name] = load_mirror(configuration, is_synthetic)

    # load filter wheel
    if "filter_wheel" in configuration["configuration"]["hardware"].keys():
        devices["filter_wheel"] = {}
        device = configuration["configuration"]["hardware"]["filter_wheel"]
        devices["filter_wheel"][device["type"]] = load_filter_wheel_connection(
            configuration, is_synthetic, plugin_devices
        )

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
