Configuring ASLM
================

In order to properly use the ASLM software you will need to configure the specifications of the various hardware that you will be using.
This is done by updating the configuration.yaml file located in either ``Users\name\AppData\Local\.ASLM`` if on Windows or ``~/.ASLM`` if on Mac/Linux.


Configuration.yaml
------------------

Hardware Section
++++++++++++++++

The first section of the file is called hardware. It contains all the necessary information to find and connect each hardware device to the computer/software.

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

Make sure that all the hardware that will be used is included as a dictionary item in yaml format.
For example, if you wanted to remove the Thorlabs stage and replace the PI stage with a different manufacturer:

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

    The type of the device is needed when deciding which Python object to instantiate on startup of the software. (eg type: ASI)
    The other fields (eg port: COM7) are specified by the manufacturer's API. They help the API communicate with the computer
    you are using which in turn allows the ASLM software to communicate with the device.

Running the software with our current microscope setup would fail. It turns out our ASI stage only moves in the x, y, z axes.
We need a way to handle theta and f axes.

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
++++++++++++++++++

The second section contains the microscopes that you will be using with the software. Each is represented as a yaml dictionary similar
to the hardware section. The GUI uses this dictionary to switch between the microscopes.

Here is an abbreviated example, the full file contains field entries for all of the hardware specified:

.. code-block:: yaml

    microscopes:
        name of microscope:

            #Other hardware

            # ...


            stage:
                hardware:
                    -
                    name: stage
                    type: ASI
                    serial_number: 123456789
                    axes: [x, y, z]
                    axes_mapping: [X, Y, Z]
                    -
                    name: stage
                    type: SyntheticStage
                    serial_number: 987654321
                    axes: [theta, f]
                y_unload_position: 10000
                y_load_position: 90000

                startfocus: 75000
                x_max: 33500
                x_min: 16000
                y_max: 100000
                y_min: 2000
                z_max: 50000
                z_min: 25000
                f_max: 100000
                f_min: -100000
                theta_max: 360
                theta_min: 0

                x_rot_position: 2000
                y_rot_position: 2000
                z_rot_position: 2000

                x_step: 500
                y_step: 500
                z_step: 500
                theta_step: 30
                f_step: 500

                position:
                    x_pos: 25250
                    y_pos: 40000
                    z_pos: 40000
                    f_pos: 70000
                    theta_pos: 0
                velocity: 1000

                x_offset: 0
                y_offset: 0
                z_offset: 0
                f_offset: 0
                theta_offset: 0

            #More hardware

            # ...


Configuring stages
^^^^^^^^^^^^^^^^^^

* The ``hardware`` dictionary ``type`` should match one of the instruments the hardware section at the top of the
configuration file.

* The ``axes`` entry explicility states the axes that the stage will control. In the Hardware Section,
we needed to add the SyntheticStage to control theta and f. In this section, we explictly give control of these axes to
the synthetic stage.

* We can optionally add ``axes_mapping`` to the hardware dictionary. ``axes_mapping`` lists the values
ASLM uses to access stage axes on the stage controller hardware, while ``axes`` tells ASLM which software axis (X, Y, Z,
Theta or Focus) is controlled by the hardware stage axis at the corresponding index of ``axes_mapping``.

* PI stages will tell you their ``axes_mapping`` in a consistent fashion if queried from their API, so we do not need to
  specify this information for a PI stage in configuration.yaml. Instead, we assume the user is aware of this mapping in
  advance (e.g., because they looked at PIMikroMove) and has passed the stage axes in axes in the order they will be found
  on the hardware controller.

* ASI stages do not provide their ``axes_mapping`` via their API, and so we do need to specify this information for ASI
  stages in ``configuration.yaml``.

* The rest of the values in the stage dictionary relate to the bounds of the physical stage. This is what the software uses
to set the minimum and maximum values for stage movement.

GUI Section
+++++++++++

The third and final section of the configuration file is the default GUI parameters.
These allow you to specify the number of GUI entries (e.g., number of channels),
spinbox intervals, and other GUI related parameters.

.. note::

    This section is still under development. The plan going forward is to have all widgets be controlled in this
    manner.

Channels
^^^^^^^^

The ``channels`` section in the GUI configuration relates to the channels tab, where
you define how you would like to acquire the data. ``interval_time`` is not yet
implemented, but will eventually allow the user to specify how frequently that
channel is acquired. For example, with an interval_time of 2, that channel will only
be acquired every other time point.

- ``count`` (int): The number of rows/channels (e.g., CH00, CH01, CH02...) available.

- ``laser_power`` (dict): Settings for laser power.

  - ``min`` (int): Minimum laser power value in percent.
  - ``max`` (int): Maximum laser power value in percent.
  - ``step`` (int): Increment step for adjusting laser power.
- ``exposure_time`` (dict): Settings for exposure time.

  - ``min`` (int): Minimum exposure time value in milliseconds.
  - ``max`` (int): Maximum exposure time value in milliseconds.
  - ``step`` (int): Increment step for adjusting exposure time.
- ``interval_time`` (dict): Settings for interval time control.

  - ``min`` (int): Minimum interval time value (inclusive).
  - ``max`` (int): Maximum interval time value (inclusive).
  - ``step`` (int): Increment step for adjusting interval time.

Stack Acquisition
^^^^^^^^^^^^^^^^^^^^^^^^

The ``stack_acquisition`` section in the GUI configuration allows you to specify
settings related to stack acquisition parameters.

- ``step_size`` (float): The step size for acquiring stack data.

  - ``min`` (float): Minimum step size value.
  - ``max`` (float): Maximum step size value.
  - ``step`` (float): Increment step for adjusting the step size.
- ``start_pos`` (int): The starting position for stack acquisition.

  - ``min`` (int): Minimum starting position value.
  - ``max`` (int): Maximum starting position value.
  - ``step`` (int): Increment step for adjusting the starting position.
- ``end_pos`` (int): The ending position for stack acquisition.

  - ``min`` (int): Minimum ending position value.
  - ``max`` (int): Maximum ending position value.
  - ``step`` (int): Increment step for adjusting the ending position.

Timepoint
^^^^^^^^^^^^^^^^^^^^^^^^

The ``timepoint`` section in the GUI configuration allows you to specify settings
related to timepoints.

- ``timepoints`` (int): The total number of timepoints.
  - ``min`` (int): Minimum timepoints value (inclusive).
  - ``max`` (int): Maximum timepoints value (inclusive).
  - ``step`` (int): Increment step for adjusting the number of timepoints.
- ``stack_pause`` (int): The pause time between stacks in milliseconds.

  - ``min`` (int): Minimum stack pause time value (inclusive).
  - ``max`` (int): Maximum stack pause time value (inclusive).
  - ``step`` (int): Increment step for adjusting the stack pause time.

Example YAML Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an example YAML configuration based on the provided settings:

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
