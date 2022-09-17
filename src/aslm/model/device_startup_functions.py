"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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


# Standard Library Imports
import platform
import sys
import logging
import time

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def auto_redial(func, args, n_tries=10, exception=Exception):
    r"""Retries connections to a startup device defined by func n_tries times.

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
    """
    val = None

    for i in range(n_tries):
        try:
            val = func(*args)
        except exception:
            if i < (n_tries-1):
                print(f"Failed {str(func)} attempt {i+1}/{n_tries}.")
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


def start_analysis(configuration,
                   use_gpu):
    r"""Initializes the analysis class on a dedicated thread

    Parameters
    ----------
    configuration : Configurator
        Configurator instance of global microscope configuration.
    use_gpu : Boolean
        Flag for enabling GPU analysis.

    Returns
    -------
    Analysis : class
        Analysis class.
    """
    from aslm.model.aslm_analysis import Analysis
    return Analysis(use_gpu)


def start_camera(configuration,
                 camera_id=0):
    r"""Initializes the camera class on a dedicated thread.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.
    experiment : dict
        Configurator instance of experiment configuration.
    camera_id : int
        Device ID (0, 1...)

    Returns
    -------
    Camera : class
        Camera class.
    """

    try:
        cam_type = configuration['configuration']['hardware']['camera'][camera_id]['type']
    except:
        cam_type = configuration['configuration']['hardware']['camera']['type']

    if cam_type == 'HamamatsuOrca':
        from aslm.model.devices.camera.camera_hamamatsu import HamamatsuOrca
        return auto_redial(HamamatsuOrca, (camera_id, configuration), exception=Exception)
    elif cam_type == 'SyntheticCamera':
        from aslm.model.devices.camera.camera_synthetic import SyntheticCamera
        return SyntheticCamera(camera_id, configuration)
    else:
        device_not_found(configuration['configuration']['hardware']['camera'])


def start_stages(configuration):
    r"""Initializes the stage class on a dedicated thread.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.

    Returns
    -------
    Stage : class
        Stage class.
    """

    stages = configuration['configuration']['hardware']['stage']

    if type(stages) == list:
        for i in range(len(stages)):
            stage_type = configuration['configuration']['hardware']['stage'][i]['type']

            if stage_type == 'PI' and platform.system() == 'Windows':
                from aslm.model.devices.stages.stage_pi import PIStage
                from pipython.pidevice.gcserror import GCSError
                return auto_redial(PIStage, (configuration,), exception=GCSError)
            elif stage_type == 'SyntheticStage':
                from aslm.model.devices.stages.stage_synthetic import SyntheticStage
                return SyntheticStage(configuration)
            else:
                device_not_found(stage_type)
    else:
        stage_type = configuration['configuration']['hardware']['stage']['type']
        if stage_type == 'PI' and platform.system() == 'Windows':
            from aslm.model.devices.stages.stage_pi import PIStage
            from pipython.pidevice.gcserror import GCSError
            return auto_redial(PIStage, (configuration,), exception=GCSError)
        elif stage_type == 'SyntheticStage':
            from aslm.model.devices.stages.stage_synthetic import SyntheticStage
            return SyntheticStage(configuration)
        else:
            device_not_found(stage_type)

def start_stages_r(configuration):
    r"""Initializes a focusing stage class in a dedicated thread.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.

    Returns
    -------
    Stage : class
        Stage class.
    """
    if configuration['configuration']['hardware']['stage'][1]['type'] == 'Thorlabs' and platform.system() == 'Windows':
        from aslm.model.devices.stages.stage_tl_kcube_inertial import TLKIMStage
        from aslm.model.devices.APIs.thorlabs.kcube_inertial import TLFTDICommunicationError
        return auto_redial(TLKIMStage, (configuration,), exception=TLFTDICommunicationError)
    else:
        device_not_found(configuration['configuration']['hardware']['stage'][1]['type'])


def start_zoom_servo(configuration):
    r"""Initializes the zoom class on a dedicated thread.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.

    Returns
    -------
    Zoom : class
        Zoom class.
    """

    if configuration['configuration']['hardware']['zoom']['type'] == 'DynamixelZoom':
        from aslm.model.devices.zoom.zoom_dynamixel import DynamixelZoom
        return auto_redial(DynamixelZoom, (configuration,), exception=RuntimeError)
    elif configuration['configuration']['hardware']['zoom']['type'] == 'SyntheticZoom':
        from aslm.model.devices.zoom.zoom_synthetic import SyntheticZoom
        return SyntheticZoom(configuration)
    else:
        device_not_found(configuration['configuration']['hardware']['zoom']['type'])


def start_filter_wheel(configuration):
    r"""Initializes the filter wheel class on a dedicated thread.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.

    Returns
    -------
    FilterWheel : class
        FilterWheel class.
    """

    if configuration['configuration']['hardware']['filter_wheel']['type'] == 'SutterFilterWheel':
        from aslm.model.devices.filter_wheel.filter_wheel_sutter import SutterFilterWheel
        return auto_redial(SutterFilterWheel, (configuration,), exception=UserWarning)
    elif configuration['configuration']['hardware']['filter_wheel']['type'] == 'SyntheticFilterWheel':
        from aslm.model.devices.filter_wheel.filter_wheel_synthetic import SyntheticFilterWheel
        return SyntheticFilterWheel(configuration)
    else:
        device_not_found(configuration['configuration']['hardware']['filter_wheel']['type'])


def start_lasers(configuration):
    r"""Initializes the laser classes on a dedicated thread.

    Currently not implemented.  Requires API development of laser communication.  Underway.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.

    Returns
    -------
    Laser : class
        Laser class.
    """

    lasers = configuration['configuration']['hardware']['lasers']
    if type(lasers) == list and lasers[0]['type'] == 'Omicron':
            # This is the Omicron LightHUB Ultra Launch - consists of both Obis and
            # Luxx lasers.
            from aslm.model.devices.APIs.coherent.ObisLaser import ObisLaser as obis
            from aslm.model.devices.APIs.omicron.LuxxLaser import LuxxLaser as luxx

            # Iteratively go through the configuration file and turn on each of the lasers,
            # and make sure that they are in appropriate external control mode.
            laser = {}
            for laser_idx in range(
                    configuration['configuration']['LaserParameters']['number_of_lasers']):
                if laser_idx == 0:
                    # 488 nm LuxX laser
                    print("Initializing 488 nm LuxX Laser")
                    comport = 'COM19'
                    laser[laser_idx] = luxx(comport)
                    laser[laser_idx].initialize_laser()

                elif laser_idx == 1:
                    # 561 nm Obis laser
                    print("Initializing 561 nm Obis Laser")
                    comport = 'COM4'
                    laser[laser_idx] = obis(comport)
                    laser[laser_idx].set_laser_operating_mode('mixed')

                elif laser_idx == 2:
                    # 642 nm LuxX laser
                    print("Initializing 642 nm LuxX Laser")
                    comport = 'COM17'
                    laser[laser_idx] = luxx(comport)
                    laser[laser_idx].initialize_laser()

                else:
                    print("Laser index not recognized")
                    sys.exit()

    elif lasers['type'] == 'SyntheticLasers':
        from aslm.model.devices.lasers.SyntheticLaser import SyntheticLaser
        laser = SyntheticLaser(configuration)

    else:
        print("Laser Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()

    return laser


def start_daq(configuration):
    r"""Initializes the data acquisition (DAQ) class on a dedicated thread.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.

    Returns
    -------
    DAQ : class
        DAQ class.
    """

    if configuration['configuration']['hardware']['daq']['type'] == 'NI':
        from aslm.model.devices.daq.daq_ni import NIDAQ
        return NIDAQ(configuration)
    elif configuration['configuration']['hardware']['daq']['type'] == 'SyntheticDAQ':
        from aslm.model.devices.daq.daq_synthetic import SyntheticDAQ
        return SyntheticDAQ(configuration)
    else:
        device_not_found(configuration['configuration']['hardware']['daq']['type'])


def start_shutters(configuration):
    r"""Initializes the shutter class on a dedicated thread.

    Initializes the shutters: ThorlabsShutter or SyntheticShutter
    Shutters are triggered via digital outputs on the NI DAQ Card
    Thus, requires both to be enabled.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.

    Returns
    -------
    Shutter : class
        Shutter class.
    """

    if configuration['configuration']['hardware']['shutters']['type'] == 'ThorlabsShutter'\
       and configuration['configuration']['hardware']['daq']['type'] == 'NI':
        from aslm.model.devices.shutter.laser_shutter_ttl import ShutterTTL
        return ShutterTTL(configuration)
    elif configuration['configuration']['hardware']['shutters']['type'] == 'SyntheticShutter':
        from aslm.model.devices.shutter.laser_shutter_synthetic import SyntheticShutter
        return SyntheticShutter(configuration)
    else:
        device_not_found(configuration['configuration']['hardware']['shutters']['type'])


def start_laser_triggers(configuration):
    r"""Initializes the laser trigger class on a dedicated thread.

    Initializes the Laser Switching, Analog, and Digital DAQ Outputs.

    Parameters
    ----------
    configuration : dict
        Configurator instance of global microscope configuration.
    experiment : dict
        Configurator instance of experiment configuration.

    Returns
    -------
    Triggers : class
        Trigger class.
    """

    if configuration['configuration']['hardware']['daq']['type'] == 'NI':
        from aslm.model.devices.lasers.laser_trigger_ni import LaserTriggers
        return LaserTriggers(configuration)
    elif configuration['configuration']['hardware']['daq']['type'] == 'SyntheticDAQ':
        from aslm.model.devices.lasers.laser_trigger_synthetic import SyntheticLaserTriggers
        return SyntheticLaserTriggers(configuration)
    else:
        device_not_found(configuration['configuration']['hardware']['daq']['type'])

def device_not_found(args):

    print("Device Not Found in Configuration.YML:", args)
    sys.exit()
