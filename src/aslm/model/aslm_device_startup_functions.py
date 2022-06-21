"""
ASLM Device Startup Functions

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


# Standard Library Imports
import platform
import sys
import logging
import time
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

# Third Party Imports

# Local Imports
# from model.devices.laser_scanning import LaserScanning


def auto_redial(func, args, n_tries=10, exception=Exception):
    """
    Retries connections to a startup device defined by func n_tries times.

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
    """
    val = None

    for i in range(n_tries):
        try:
            val = func(*args)
        except exception:
            if i < (n_tries-1):
                print(f"Failed {str(func)} attempt {i+1}/{n_tries}.")
                time.sleep(0.1)
            else:
                raise exception
        else:
            break

    return val

def start_analysis(configuration, experiment, use_gpu, verbose):
    """
    # Initializes the analysis class on a dedicated thread
    """
    from model.aslm_analysis import Analysis
    return Analysis(use_gpu, verbose)

def start_camera(configuration, experiment, verbose):
    """
    # Initializes the camera as a sub-process using concurrency tools.
    """

    if configuration.Devices['camera'] == 'HamamatsuOrca':
        from model.devices.cameras import HamamatsuOrca
        return auto_redial(HamamatsuOrca, (0, configuration, experiment, verbose), exception=AttributeError)
    elif configuration.Devices['camera'] == 'SyntheticCamera':
        from model.devices.cameras import SyntheticCamera
        return SyntheticCamera(0, configuration, experiment, verbose)
    else:
        device_not_found(configuration.Devices['camera'])


def start_stages(configuration, verbose):
    """
    # Initializes the Stage.
    """


    if configuration.Devices['stage'] == 'PI' and platform.system(
    ) == 'Windows':
        from model.devices.stages import PIStage
        return PIStage(configuration, verbose)
    elif configuration.Devices['stage'] == 'SyntheticStage':
        from model.devices.stages import SyntheticStage
        return SyntheticStage(configuration, verbose)
    else:
        device_not_found(configuration.Devices['stage'])


def start_zoom_servo(configuration, verbose):
    """
    # Initializes the Zoom Servo Motor. DynamixelZoom of SyntheticZoom
    """

    if configuration.Devices['zoom'] == 'DynamixelZoom':
        from model.devices.zoom import DynamixelZoom
        return DynamixelZoom(configuration, verbose)
    elif configuration.Devices['zoom'] == 'SyntheticZoom':
        from model.devices.zoom import SyntheticZoom
        return SyntheticZoom(configuration, verbose)
    else:
        device_not_found(configuration.Devices['zoom'])


def start_filter_wheel(configuration, verbose):
    """
    # Initializes the Filter Wheel. Sutter or SyntheticFilterWheel
    """

    if configuration.Devices['filter_wheel'] == 'SutterFilterWheel':
        from model.devices.filter_wheels import SutterFilterWheel
        return auto_redial(SutterFilterWheel, (configuration, verbose), exception=UserWarning)
    elif configuration.Devices['filter_wheel'] == 'SyntheticFilterWheel':
        from model.devices.filter_wheels import SyntheticFilterWheel
        return SyntheticFilterWheel(configuration, verbose)
    else:
        device_not_found(configuration.Devices['filter_wheel'])


def start_lasers(configuration, verbose):
    '''
    # Start the lasers: Lasers or SyntheticLasers
    '''

    if configuration.Devices['lasers'] == 'Omicron':
        # This is the Omicron LightHUB Ultra Launch - consists of both Obis and
        # Luxx lasers.
        from model.devices.lasers.coherent.ObisLaser import ObisLaser as obis
        from model.devices.lasers.omicron.LuxxLaser import LuxxLaser as luxx

        # Iteratively go through the configuration file and turn on each of the lasers,
        # and make sure that they are in appropriate external control mode.
        laser = {}
        for laser_idx in range(
                configuration.LaserParameters['number_of_lasers']):
            if laser_idx == 0:
                # 488 nm LuxX laser
                print("Initializing 488 nm LuxX Laser")
                comport = 'COM19'
                laser[laser_idx] = luxx(comport, verbose)
                laser[laser_idx].initialize_laser()

            elif laser_idx == 1:
                # 561 nm Obis laser
                print("Initializing 561 nm Obis Laser")
                comport = 'COM4'
                laser[laser_idx] = obis(comport, verbose)
                laser[laser_idx].set_laser_operating_mode('mixed')

            elif laser_idx == 2:
                # 642 nm LuxX laser
                print("Initializing 642 nm LuxX Laser")
                comport = 'COM17'
                laser[laser_idx] = luxx(comport, verbose)
                laser[laser_idx].initialize_laser()

            else:
                print("Laser index not recognized")
                sys.exit()

    elif configuration.Devices['lasers'] == 'SyntheticLasers':
        from model.devices.lasers.SyntheticLaser import SyntheticLaser
        laser = SyntheticLaser(configuration, verbose)

    else:
        print("Laser Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()

    if verbose:
        print("Initialized ", configuration.Devices['lasers'])

    return laser


def start_daq(configuration, experiment, etl_constants, verbose):
    """
    # Start the data acquisition device (DAQ):  NI or SyntheticDAQ
    """

    if configuration.Devices['daq'] == 'NI':
        from model.devices.daq import NIDAQ
        return NIDAQ(configuration, experiment, etl_constants, verbose)
    elif configuration.Devices['daq'] == 'SyntheticDAQ':
        from model.devices.daq import SyntheticDAQ
        return SyntheticDAQ(configuration, experiment, etl_constants, verbose)
    else:
        device_not_found(configuration.Devices['daq'])


def start_shutters(configuration, experiment, verbose):
    """
    # Initializes the shutters: ThorlabsShutter or SyntheticShutter
    # Shutters are triggered via digital outputs on the NI DAQ Card
    # Thus, requires both to be enabled.
    """

    if configuration.Devices['shutters'] == 'ThorlabsShutter' and configuration.Devices['daq'] == 'NI':
        from model.devices.laser_shutters import ThorlabsShutter
        return ThorlabsShutter(configuration, experiment, verbose)
    elif configuration.Devices['shutters'] == 'SyntheticShutter':
        from model.devices.laser_shutters import SyntheticShutter
        return SyntheticShutter(configuration, experiment, verbose)
    else:
        device_not_found(configuration.Devices['shutters'])


def start_laser_triggers(configuration, experiment, verbose):
    """
    # Initializes the Laser Switching, Analog, and Digital DAQ Outputs:
    """

    if configuration.Devices['daq'] == 'NI':
        from model.devices.laser_triggers import LaserTriggers
        return LaserTriggers(configuration, experiment, verbose)
    elif configuration.Devices['daq'] == 'SyntheticDAQ':
        from model.devices.laser_triggers import SyntheticLaserTriggers
        return SyntheticLaserTriggers(configuration, experiment, verbose)
    else:
        device_not_found(configuration.Devices['daq'])


def start_laser_scanning(configuration, experiment, etl_constants, verbose):
    """
    # Initializes the Laser Switching, Analog, and Digital DAQ Outputs:
    """

    if configuration.Devices['daq'] == 'NI':
        return LaserScanning(configuration, experiment, etl_constants, verbose)
    elif configuration.Devices['daq'] == 'SyntheticDAQ':
        return SyntheticLaserTriggers(
            configuration, experiment, etl_constants, verbose)
    else:
        device_not_found(configuration.Devices['daq'])


def device_not_found(args):

    print("Device Not Found in Configuration.YML:", args)
    sys.exit()
