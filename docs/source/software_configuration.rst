Configuration Overview
=========================

This section outlines the ``configuration.yaml``, ``experiment.yaml``,``rest_api_config.yaml``,  ``waveform_templates.yaml``, and ``waveform_constants.yaml``
files. Once you are ready to configure your exact hardware, please see the :doc:`Supported Hardware
<supported_hardware>` section.


Configuration File
------------------
In order for the ASLM software to function, you will need to configure the
specifications of the various hardware that you will be using. The first time you
launch the software, ASLM will evaluate the the hardware settings as provided in the
``ASLM\config\configuration.yaml`` file. Every subsequent time you launch the
software, a local version of the ``configuration.yaml`` file can be found
in either ``Users\name\AppData\Local\.ASLM\config`` if on Windows or ``~/.ASLM`` if on
Mac/Linux.

To avoid confusion, we recommend launching the software in the synthetic hardware
mode initially. Within your Terminal, or Anaconda Prompt, activate your ASLM Python
environment and launch the software by typing: ``aslm -sh``. Thereafter, you should
only modify the ``configuration.yaml`` file in your local ``/.ASLM`` directory. The
local copy avoids conflicts between different microscopes after pulling new
changes on GitHub.


Hardware Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The first section of the file is called hardware. It contains all the necessary
information to find and connect each hardware device to the computer/software.

Here is an example of what the section will look like:

.. code-block:: yaml

    # Configuration in YAML
    hardware:
        daq:
            type: NI
        camera:
            -
              type: HamamatsuOrca
              serial_number: 302158
            -
              type: HamamatsuOrca
              serial_number: 302352
        filter_wheel:
            type: SutterFilterWheel
            port: COM19
            baudrate: 9600
            number_of_wheels: 2
        stage:
            -
              type: PI
              controllername: 'C-884'
              stages: L-509.20DG10 L-509.40DG10 L-509.20DG10 M-060.DG M-406.4PD NOSTAGE
              refmode: FRF FRF FRF FRF FRF FRF
              serial_number: 119060508
            -
              type: Thorlabs
              serial_number: 74000375
        zoom:
            type: DynamixelZoom
            servo_id: 1
            port: COM18
            baudrate: 1000000

Make sure that all the hardware that will be used is included as a dictionary item in
yaml format. For example, if you wanted to remove the Thorlabs stage and replace the
PI stage with a different manufacturer:

.. code-block:: yaml

    stage:
        type: ASI
        serial_number: 123456789
        port: COM7
        baudrate: 115200

You would add it to the hardware section:


.. code-block:: yaml

    # Configuration in YAML
    hardware:
        daq:
            type: NI
        camera:
            -
              type: HamamatsuOrca
              serial_number: 302158
            -
              type: HamamatsuOrca
              serial_number: 302352
        filter_wheel:
            type: SutterFilterWheel
            port: COM19
            baudrate: 9600
            number_of_wheels: 2
        stage:
            type: ASI
            serial_number: 123456789
            port: COM7
            baudrate: 115200
        zoom:
            type: DynamixelZoom
            servo_id: 1
            port: COM18
            baudrate: 1000000

.. note::

    The type of the device is needed when deciding which python object to instantiate
on startup of the software (eg type: ASI). The other fields are specified by the
manufacturers API software. They help the API software communicate with the computer
you are using which in turn allows the ASLM software to communicate with the device
(eg port: COM7).

Running the software with our current microscope setup would fail. It turns out our
ASI stage only moves in the x, y, z axes. We need a way to handle theta and f axes.

To do this we will employ the SyntheticStage:

.. code-block:: yaml

    # Configuration in YAML
    hardware:
        daq:
            type: NI
        camera:
            -
              type: HamamatsuOrca
              serial_number: 302158
            -
              type: HamamatsuOrca
              serial_number: 302352
        filter_wheel:
            type: SutterFilterWheel
            port: COM19
            baudrate: 9600
            number_of_wheels: 2
        stage:
            -
              type: ASI
              serial_number: 123456789
              port: COM7
              baudrate: 115200
            -
              type: SyntheticStage
              serial_number: 987654321
        zoom:
            type: DynamixelZoom
            servo_id: 1
            port: COM18
            baudrate: 1000000

.. note::

    Notice how there are two entries in the stage field. Each field that you need to add to a section is done by placing a '-'
    and then the information below that. This formats the stage field to behave like a python list in the code.

If your microscope system does not have a device listed in the hardware section using the Synthetic typing will allow the software to run without it.
Another example would be replacing the zoom type with SyntheticZoom in the instance your microscope does not use that hardware. Your system will still run as you expect.

Microscope Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The second section contains the microscopes that you will be using with the software.
Each is represented as a yaml dictionary similar to the hardware section. The GUI
uses this dictionary to switch between the microscopes, each with their own hardware
and operating modes:

.. code-block:: yaml

    microscopes:
        name of microscope 1:
            ...
            ...
        name of microscope 2:
            ...
            ...

DAQ Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    microscopes:
        name of microscope 1:
            daq
                hardware
                    name
                    type
            sample_rate
            sweep_time
            master_trigger_out_line
            camera_trigger_out_line
            trigger_source
            laser_port_switcher
            laser_switch_state

Camera Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    microscopes:
        name of microscope 1:
            camera:
                hardware
                    name
                    type
                    serial_number
                x_pixels: 2048.0
                y_pixels: 2048.0
                pixel_size_in_microns: 6.5
                subsampling: [1, 2, 4]
                sensor_mode: Normal  # 12 for progressive, 1 for normal. Normal/Light-Sheet
                readout_direction: Top-to-Bottom  # Top-to-Bottom', 'Bottom-to-Top'
                lightsheet_rolling_shutter_width: 608
                defect_correct_mode: 2.0
                binning: 1x1
                readout_speed: 1.0
                trigger_active: 1.0
                trigger_mode: 1.0 # external light-sheet mode
                trigger_polarity: 2.0  # positive pulse
                trigger_source: 2.0  # 2 = external, 3 = software.
                exposure_time: 20 # Use milliseconds throughout.
                delay_percent: 10
                pulse_percent: 1
                line_interval: 0.000075
                display_acquisition_subsampling: 4
                average_frame_rate: 4.969
                frames_to_average: 1
                exposure_time_range:
                    min: 1
                    max: 1000
                    step: 1


Remote Focus Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    microscopes:
        name of microscope 1:
            remote_focus_device:
                hardware:
                    name: daq
                    type: NI
                    channel: PXI6259/ao2
                    min: 0
                    max: 5
                delay_percent: 7.5
                ramp_rising_percent: 85
                ramp_falling_percent: 2.5
                amplitude: 0.7
                offset: 2.3
                smoothing: 0.0


Galvo Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    microscopes:
        name of microscope 1:
            galvo:
                -
                    hardware:
                        name: daq
                        type: NI
                        channel: PXI6259/ao0
                        min: -5
                        max: 5
                    waveform: sine
                    frequency: 99.9
                    amplitude: 2.5
                    offset: 0.5
                    duty_cycle: 50
                    phase: 1.57079 # pi/2


Filter Wheel Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    microscopes:
        name of microscope 1:
            filter_wheel:
                hardware:
                    name: filter_wheel
                    type: SutterFilterWheel
                    wheel_number: 1
                filter_wheel_delay: .030 # in seconds
                available_filters:
                    Empty-Alignment: 0
                    GFP - FF01-515/30-32: 1
                    RFP - FF01-595/31-32: 2
                    Far-Red - BLP01-647R/31-32: 3
                    Blocked1: 4
                    Blocked2: 5
                    Blocked3: 6
                    Blocked4: 7
                    Blocked5: 8
                    Blocked6: 9


Stage Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The stage field has a hardware section that should reflect similar values to the hardware section at the top of the
configuration file. The only difference is the axes entry that explicility states the axes that the stage will control.
This lines up with earlier, we needed to add the SyntheticStage to control theta and f. The rest of the values in the
stage field relate to the bounds of the physical stage. This is what the software uses to set the minimum and maximum values
for stage movement. Most stages will have different values respectively.


.. code-block:: yaml

    microscopes:
        name of microscope 1:
            stage:
                hardware:
                    -
                        name: stage
                        type: PI
                        serial_number: 119060508
                        axes: [x, y, z, theta, f]
                        volts_per_micron: None
                        axes_channels: None
                        max: None
                        min: None

                joystick_axes: [x, y, z]
                x_max: 100000
                x_min: -100000
                y_max: 100000
                y_min: -100000
                z_max: 100000
                z_min: -100000
                f_max: 100000
                f_min: -100000
                theta_max: 360
                theta_min: 0

                x_step: 500
                y_step: 500
                z_step: 500
                theta_step: 30
                f_step: 500
                velocity: 1000

                x_offset: 0
                y_offset: 0
                z_offset: 0
                theta_offset: 0
                f_offset: 0

Stage Axes Definition
"""""""""""""""""""""""
Many times, the coordinate system of the stage hardware do not agree with the optical
definition of each axes identity. For example, many stages define their vertical
dimension as `z`, whereas optically, we often define this axis as `x`. Thus, there is
often a need to map the mechanical axes to the optical axes, and this is done with
the axes mapping dictionary entry in the stage hardware section. By default, stage axes are
read in as `x`, `y`, `z`, `theta`, `f`, where theta is rotation and f is focus, but this 
can be changed by changing axes mapping.

.. code-block:: yaml

    axes: [x, y, z, theta, f]
    axes_mapping: [x, y, z, theta, f]

If, on a certain microscope, the z stage axis corresponds to the optical y axis, 
and vice versa, you would then have to import the stages as following:

.. code-block:: yaml

    axes: [x, y, z, theta, f]
    axes_mapping: [x, z, y, theta, f]

Joystick Axes Definition
""""""""""""""""""""""""
If you are using a joystick, it is possible to disable GUI control of the stage axes 
that the joystick can interact with. The axes that the joystick can interact with 
appear in the stage field as following:

.. code-block:: yaml

    joystick_axes: [x, y, z]

Note that these axes should agree with the optical axes. If, on the same microscope 
as mentioned in the Stage Axes Definition section, the joystick were to control 
the optical y axis corresponding to the stage z axis, you would have to put `y` in 
the joystick axes brackets as following:

.. code-block:: yaml

    joystick_axes: [y]



Zoom Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    microscopes:
        name of microscope 1:
            zoom:
                hardware:
                    name: zoom
                    type: DynamixelZoom
                    servo_id: 1
                position:
                    0.63x: 0
                    1x: 627
                    2x: 1711
                    3x: 2301
                    4x: 2710
                    5x: 3079
                    6x: 3383
                pixel_size:
                    0.63x: 9.7
                    1x: 6.38
                    2x: 3.14
                    3x: 2.12
                    4x: 1.609
                    5x: 1.255
                    6x: 1.044
                stage_positions:
                    BABB:
                        f:
                            0.63x: 0
                            1x: 1
                            2x: 2
                            3x: 3
                            4x: 4
                            5x: 5
                            6x: 6

Shutter Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    microscopes:
        name of microscope 1:
            shutter:
                hardware:
                name: daq
                type: NI
                channel: PXI6259/port0/line0
                min: 0
                max: 5

Laser Section
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    microscopes:
        name of microscope 1:
            lasers:
                - wavelength: 488
                    onoff:
                        hardware:
                            name: daq
                            type: NI
                            channel: PXI6733/port0/line2
                            min: 0
                            max: 5
                    power:
                        hardware:
                            name: daq
                            type: NI
                            channel: PXI6733/ao0
                            min: 0
                            max: 5
                    type: LuxX
                    index: 0
                    delay_percent: 10
                    pulse_percent: 87
                - wavelength: ...




GUI Section
------------------

The third and final section of the configuration file is the GUI parameters.

It will look something like the below:

.. code-block:: yaml

    gui:
        channels:
            count: 5
            laser_power:
            min: 0
            max: 100
            step: 10
            exposure_time:
            min: 1
            max: 1000
            step: 5
            interval_time:
            min: 0
            max: 1000
            step: 5
        stack_acquisition:
            step_size:
            min: 0.200
            max: 1000
            step: 0.1
            start_pos:
            min: -5000
            max: 5000
            step: 1
            end_pos:
            min: -5000
            max: 10000
            step: 1
        timepoint:
            timepoints:
            min: 1
            max: 1000
            step: 1
            stack_pause:
            min: 0
            max: 1000
            step: 1

The values in each field relate to GUI widgets. They will set the min, max and step size for each of the
respective spinboxes in the example above.

.. note::

    This section is still under development. The plan going forward is to have all widgets be controlled in this
    manner.

Waveform Constants File
------------------------
In progress...

Remote Constants Section
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    "remote_focus_constants": {
        "microscope name 1": {
            "0.63x": {
                "488nm": {
                    "amplitude": "2.5",
                    "offset": "2.336",
                    "percent_smoothing": "0",
                    "percent_delay": "0"
                },
                "562nm": {
                    "amplitude": "2.5",
                    "offset": "2.336",
                    "percent_smoothing": "0",
                    "percent_delay": "0"
                },
                "642nm": {
                    "amplitude": "2.5",
                    "offset": "2.336",
                    "percent_smoothing": "0",
                    "percent_delay": "0"
                }
            },
            ...
        }
    },


Galvo Constants Section
^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

    ...
    "galvo_constants": {
        "Galvo 0": {
            "Nanoscale": {
                "N/A": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                }
            },
            "Mesoscale": {
                "0.63x": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                },
                "1x": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                },
                "2x": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                },
                "3x": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                },
                "4x": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                },
                "5x": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                },
                "6x": {
                    "amplitude": "0.11",
                    "offset": "0.10",
                    "frequency": "99"
                }
            }
        }
    },
    ...

Other Constants Section
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    "other_constants": {
        "duty_wait_duration": "10"
    }



Waveform Templates File
----------------------------
In progress...


.. code-block::

    {
      "Default": {
        "repeat": 1,
        "expand": 1,
      },
      "Confocal-Projection": {
        "repeat": timepoints,
        "expand": n_plane,
      }
    }

Rest API Configuration File
--------------------------------------------------------
In progress...

.. code-block::

    %YAML 1.2
    ---
    Ilastik:
      url: 'http://127.0.0.1:5000/ilastik'
