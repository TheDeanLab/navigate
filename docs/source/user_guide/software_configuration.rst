======================
Configuration Overview
======================

This section outlines the ``configuration.yaml``, ``experiment.yml``,
``rest_api_config.yml``, ``waveform_templates.yml``, and
``waveform_constants.yml`` files.

-----------------

Configuration File
==================
In order for the **navigate** software to function, you will need to configure the
specifications of the various hardware that you will be using. The first time you
launch the software, **navigate** will create a copy of the
``navigate\config\configuration.yaml`` and the rest of the configuration files in
``C:\Users\Username\AppData\Local\.navigate\config`` on  Windows or ``~/.navigate`` on
Mac/Linux. **navigate** uses these local copies of the configuration files to store
information specific to the setup attached to the computer it is installed on.

To avoid confusion, we recommend launching the software in the synthetic hardware
mode initially. Within your Terminal, or Anaconda Prompt, activate your **navigate** Python
environment and launch the software by typing: ``navigate -sh``. Thereafter, you should
only modify the ``configuration.yaml`` file in your local ``.navigate`` directory. The
local copy avoids conflicts between different microscopes after pulling new
changes on GitHub.

.. tip::

    Once **navigate** is open in the synthetic hardware mode, you can open the
    ``configuration.yaml`` file by going to :menuselection:`File` menu and selecting
    :ref:`Open Configuration Files <user_guide/gui_walkthrough:file>`.

It may help to open
``C:\Users\Username\AppData\Local\.navigate\config\configuration.yaml`` and follow
along in this file when reading the next sections.

See the :ref:`Setting up an Axially Swept Light-Sheet Microscope <setup_aslm>` case
study for a general walkthrough of how to build your own configuration file and see
:doc:`Implementations <hardware/implementations>` for examples of configuration files.

-----------------

.. _hardware_section:

Hardware Section
----------------
The first section of the ``configuration.yaml`` file is called ``hardware``. It contains
all the necessary information to find and connect each hardware device to the
computer/software.

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

This example specifies that we are connected to

* A National Instruments DAQ (possibly multiple).
* Two Hamamatsu Orca (Flash or Fusion) cameras with different serial numbers for
  identification.
* A Sutter filter wheel controller connected via USB on port ``COM19``. This control two
  filter wheels.
* A Physik Instrumente controller, identified by serial number, with access to 5 stages in ``FRF`` refrence mode
  (see PI's documentation).
* A Thorlabs stage (with a single axis), identified by a serial number.
* A Dynamixel zoom device connected via USB on port ``COM18``.

Make sure that the ``configuration.yaml`` specifies the hardware on your microscope.
For example, if you wanted to remove the Thorlabs stage and replace the PI stage with
an ASI stage, the ``stage`` section would instead read:

.. code-block:: yaml

    stage:
        type: ASI
        serial_number: 123456789
        port: COM7
        baudrate: 115200

Notice that since we are now using a single stage, we no longer have a ``-`` above the
stage entry. The ``-`` indicates a list, and is only needed if we want to load multiple
types of a single hardware.

.. note::

    The type of the device is needed when deciding which Python object to instantiate
    on startup of the software (eg ``type: ASI``). The other fields (eg ``port: COM7``)
    change depending on the manufacturer's API. They help the API communicate with the
    computer you are using, which in turn allows the **navigate** software to communicate
    with the device.

Running the software with our current microscope setup would fail. It turns out our
ASI stage only moves in the ``x``, ``y``, ``z`` and ``f`` axes. Later, you will see we need a way to
handle ``theta`` axis. To address this, we will change our ``stage`` block of the YAML to
also load a ``SyntheticStage``:

.. code-block:: yaml

    stage:
        -
            type: ASI
            serial_number: 123456789
            port: COM7
            baudrate: 115200
        -
            type: SyntheticStage
            serial_number: 987654321

If your microscope system does not have a device listed in the hardware section using
the Synthetic typing will allow the software to run without it. Another example would
be replacing the zoom type with ``SyntheticZoom`` in the instance your microscope does
not use that hardware. Your system will still run as you expect.

-----------------

Microscope Section
------------------

The second section of ``configuration.yaml`` contains the microscope configurations
that you will be using with the software. Each microscope is represented as a YAML
dictionary, as in the hardware section. This section enables us to load one or more
microscopes using the same hardware with varying combinations:

.. code-block:: yaml

    microscopes:
        microscope1:
            ...
            ...
        microscope2:
            ...
            ...

Where ``microscope1`` and ``microscope2`` are names of two different microscopes using
different combinations of the hardware listed in the ``hardware`` section. The names of
the microscopes must not include spaces or special characters such as ``<``, ``\``,
``#``, ``%``, or ``?``.

Each microscope is expected to have a ``daq``, ``camera``, ``remote_focus_device``,
``galvo``, ``filter_wheel``, ``stage``, ``zoom``, ``shutter`` and ``lasers`` section of
the YAML dictionary. As in the hardware section, unused devices can be specified as
synthetic.

Most of the information to set up these devices can be found in the
:doc:`Supported Hardware <hardware/supported_hardware>` section of the documentation.
Additional explanations of a few specific sections of the microscope configuration are
below. Notably, the ``zoom`` section of the ``configuration.yaml`` specifies effective
pixel size.

-----------------

Stage Subsection
^^^^^^^^^^^^^^^^

The stage section of the microscope 1) puts the stage control from the ``hardware``
section into the microscope 2) sets boundaries for stage movement and 3) optionally
specifies joystick-controlled axes.

.. code-block:: yaml

    microscopes:
        microscope1:
            stage:
            hardware:
                -
                    name: stage
                    type: ASI
                    serial_number: 123456789
                    axes: [x, y, z, f] # Software
                    axes_mapping: [M, Y, X, Z] # M Shear axis mapping


                -
                    name: stage
                    type: SyntheticStage
                    serial_number: 987654321
                    axes: [theta]

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

            x_offset: 0
            y_offset: 0
            z_offset: 0
            theta_offset: 0
            f_offset: 0

First we set the axes controlled by each piece of hardware and a mapping from the
hardware's API axes to our software's axes. For example, the ASI ``M`` axis is mapped
onto our software's ``x`` axis below.

As you may recall from the :ref:`Hardware Section <hardware_section>`, we needed to
add the ``SyntheticStage`` to control ``theta``. We now specify in the microscope that
``theta`` is controlled by the synthetic stage in the ``hardware`` section of
``microscope1``.

Below this, we specify that only ``x``, ``y`` and ``z`` axes may be controlled by a joystick and
we set the stage bounds for each of the axes.

Finally, we set the offset for each stage axis. This is an offset relative to other
microscopes (e.g. ``microscope2``) specified in ``configuration.yaml``. In this case,
``microscope1`` is the reference microscope. Additional microscopes may ask the stage
to move to a different offset in order to observe the sample at the same position as
``microscope1``.

-----------------

Stage Axes Definition
"""""""""""""""""""""

Many times, the coordinate system of the stage hardware do not agree with the optical
definition of each axes identity. For example, many stages define their vertical
dimension as ``z``, whereas optically, we often define this axis as ``x``. Thus, there is
often a need to map the mechanical axes to the optical axes, and this is done with
the ``axes_mapping`` dictionary entry in the stage hardware section. By default, stage axes
are read in as ``x``, ``y``, ``z``, ``theta``, ``f``, where ``theta`` is rotation and ``f``
is focus, but this can be changed by changing axes mapping.

.. code-block:: yaml

    axes: [x, y, z, theta, f]
    axes_mapping: [x, y, z, r, f]

If, on a certain microscope, the ``z`` stage axis corresponds to the optical y-axis,
and vice versa, you would then have to import the stages as following:

.. code-block:: yaml

    axes: [x, y, z, theta, f]
    axes_mapping: [x, z, y, r, f]

-----------------

Joystick Axes Definition
""""""""""""""""""""""""

If you are using a joystick, it is possible to disable GUI control of the stage axes
that the joystick can interact with. The axes that the joystick can interact with
appear in the stage field as following:

.. code-block:: yaml

    joystick_axes: [x, y, z]

.. Note::

    These axes should agree with the optical axes. If, on the same microscope
    as mentioned in the Stage Axes Definition section, the joystick were to control
    the optical y-axis corresponding to the stage z axis, you would have to put ``y`` in
    the joystick axes brackets as following:

.. code-block:: yaml

    joystick_axes: [y]

-----------------

Zoom Subsection
^^^^^^^^^^^^^^^

The ``zoom`` section of ``configuration.yaml`` specifies control over microscope
zoom lenses. For example, we use the
`Dynamixel Smart Actuator <https://www.dynamixel.com/>`_ to control the rotating
zoom wheel on an Olympus MVXPLAPO 1x/0.25.

.. code-block:: yaml

    microscopes:
        microscope1:
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


The ``hardware`` section connects to the zoom hardware. The ``positions`` specify the
voltage of the actuator at different zoom positions. The ``pixel_size`` specifies the
effective pixel size of the system at each zoom. The ``stage_positions`` account for
focal shifts in between the different zoom values (the MVXPLAPO does not have a
consistent focal plane). These may change depending on the immersion media. Here it is
specified for a ``BABB`` (Benzyl Alcohol Benzyl Benzoate) immersion media.

Regardless of whether or not your microscope uses a zoom device, you must have a
``zoom`` entry, indicating the effective pixel size of your system in micrometers.
For example,

.. code-block:: yaml

    zoom:
      hardware:
        name: zoom
        type: SyntheticZoom
        servo_id: 1
      position:
        N/A: 0
      pixel_size:
        N/A: 0.168

-----------------

GUI Section
-----------

The third and final section of the ``configuration.yaml`` file is the GUI parameters.

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

The values in each field relate to GUI widgets.

- The ``channels`` section indicates GUI settings for the channel settings under
  :guilabel:`Channels`, :guilabel:`Channel Settings`.
    - `count` specifies how many channels should be displayed.
    - `laser_power`, `exposure_time` and `interval_time` are used to set
      the minimum, maximum and step size values for :guilabel:`Power`,
      :guilabel:`Exp. Time (ms)` and :guilabel:`Interval`, respectively.

- The ``stack_acquisition`` section indicates GUI settings for the stack acquisition
  settings under :guilabel:`Channels`, :guilabel:`Stack Acquisition Settings (um)`.
    - `step_size`, `start_pos` and `end_pos` are used to set the minimum, maximum and step
      size values for :guilabel:`Step Size`, :guilabel:`Start` and :guilabel:`End`,
      respectively.

- The ``timepoint`` section indicates GUI settings for the timepoint
  settings under :guilabel:`Channels`, :guilabel:`Timepoint Settings`.
    - `timepoints` and `stack_pause` are used to set the minimum, maximum and step
      size values for :guilabel:`Timepoints` and :guilabel:`Stack Pause (s)`,
      respectively.

.. note::

    This section is still under development. The plan going forward is to have all
    widgets be controlled in this manner.

-----------------

Experiment File
===============

The ``experiment.yml`` file stores information about the current state of the program.
This includes laser and camera parameters, saving options, z-stack settings and much
more. This file does not need to be edited by the user. The program will update it
automatically and save changes automatically on exit.

-----------------

Waveform Constants File
=======================

The ``waveform_constants.yml`` file stores the waveform parameters that can be edited
by going to :menuselection:`Microscope Configuration --> Waveform Parameters`. This
file does not need to be edited by the user. The program will update it automatically
and save changes automatically on exit.

-----------------

Waveform Templates File
=======================

The waveform templates file stores default behavior for the number of repeats for
specific waveforms. This file only needs to be edited if the user wishes to introduce
a new waveform behavior to the application.

-----------------

Rest API Configuration File
===========================

The REST API configuration file specifies where the REST API should look to get
and post data. This is only needed if you are using a plugin that requires the
REST API, such as our communication with `ilastik <https://www.ilastik.org>`_.
