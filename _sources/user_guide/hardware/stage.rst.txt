======
Stages
======

Our software empowers users with a flexible solution for configuring
multiple stages, catering to diverse microscope modalities. Each stage can be
customized to suit the specific requirements of a particular modality or shared
across  various modalities. Our unique approach allows seamless integration of stages
from different manufacturers, enabling users to mix and match components for a truly
versatile and optimized setup tailored to their research needs.

.. Note::
    The software provides configure specific hardware axes to software axes. This is
    specified in the configuration file. For example, if specified as follows, the software
    x, y, z, and f axes can be mapped to the hardware axes M, Y, X, and Z, respectively.

    .. code-block:: yaml

        axes: [x, y, z, f]
        axes_mapping: [M, Y, X, Z]

------------------

Applied Scientific Instrumentation
----------------------------------

Tiger Controller
~~~~~~~~~~~~~~~~


The ASI `Tiger Controller <https://www.asiimaging.com/controllers/tiger-controller/>`_. is
a multi-purpose controller for ASI stages, filter wheels, dichroic sliders,
and more. We communicate with Tiger Controllers via a serial port. It is recommended that you
first establish communication with the device using `ASI provided software <https://asiimaging.com/docs/products/tiger>`_.

.. note::

    **navigate** has been tested with the following versions of the ASI's Tiger
    Controller software:

    - Tiger Controller 2.2.0.



.. warning::
    If you are using the FTP-2000 stage, do not change the F stage axis. This
    will differentially drive the two vertical posts, causing them to torque and
    potentially damage one another.

.. tip::
    ASI stage's include a configuration option, ``feedback_alignment``, which
    corresponds to the `Tiger Controller AA Command <https://asiimaging.com/docs/commands/aalign>`_.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: ASI
                  serial_number: 001
                  axes: [x, y, z, theta, f]
                  axes_mapping: [A, B, C, D, E]
                  feedback_alignment: [90, 90, 90, 5, 90]
                  volts_per_micron: 0.0
                  min: 0.0
                  max: 1.0
                  controllername:
                  stages:
                  refmode:
                  port: COM12
                  baudrate: 9600
                  timeout: 0.25
              joystick_axes: [x, y, z]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False


MFC2000
~~~~~~~


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: MFC2000
                  serial_number: 001
                  axes: [x, y, z, theta, f]
                  axes_mapping: [A, B, C, D, E]
                  feedback_alignment: [90, 90, 90, 5, 90]
                  volts_per_micron: 0.0
                  min: 0.0
                  max: 1.0
                  controllername:
                  stages:
                  refmode:
                  port: COM12
                  baudrate: 9600
                  timeout: 0.25
              joystick_axes: [x, y, z]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|


MS2000
~~~~~~~


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: MS2000
                  serial_number: 001
                  axes: [x, y, z, theta, f]
                  axes_mapping: [A, B, C, D, E]
                  feedback_alignment: [90, 90, 90, 5, 90]
                  volts_per_micron: 0.0
                  min: 0.0
                  max: 1.0
                  controllername:
                  stages:
                  refmode:
                  port: COM12
                  baudrate: 9600
                  timeout: 0.25
              joystick_axes: [x, y, z]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|

------------------

Sutter Instruments
-------------

MP-285
~~~~~~

The `Sutter MP-285 <https://www.sutter.com/MICROMANIPULATION/mp285.html>`_ communicates
via serial port and is quite particular. We have done our best to ensure the
communication is stable, but occasionally the stage will send or receive an extra
character, throwing off communication. In this case, the MP-285's screen will be
covered in 0s, 1s or look garbled. If this happens, simply turn off the software,
power cycle the stage, and press the "MOVE" button on the MP-285 controller once. When
the software is restarted, it should work.

.. tip::

  Sometimes the Coherent Connection software messes with the MP-285 serial
  communication if it is connected to the lasers.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: MP285
                  serial_number: 001
                  axes: [x, y, z]
                  axes_mapping: [x, y, z]
                  feedback_alignment: 
                  volts_per_micron: 0.0
                  min: 0.0
                  max: 25000
                  controllername:
                  stages:
                  refmode:
                  port: COM1
                  baudrate: 9600
                  timeout: 0.25
              joystick_axes: [x, y, z]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|

Physik Instrumente
------------------

These stages are controlled by `PI <https://www.pi-usa.us/en/>`_'s own
`Python code <https://pypi.org/project/PIPython/>`_ and are quite stable.

.. note::

    **navigate** has been tested with the following versions of the Physik
    Instrumente software and drivers:

    - PIMikroMove: 2.36.1.0
    - PI_GCS2_DLL: 3.22.0.0


They
include a special ``hardware`` option, ``refmode``, which corresponds to how the
PI stage chooses to self-reference. Options are ``REF``, ``FRF``, ``MNL``, ``FNL``,
``MPL`` or ``FPL``. These are PI's GCS commands, and the correct reference mode
for your stage should be found by launching PIMikroMove, which should come with
your stage. Stage names (e.g. ``L-509.20DG10``) can also be found in PIMikroMove
or on a label on the side of your stage.

.. note::
    PI L-509.20DG10 has a unidirectional repeatability of 100 nm, bidirectional
    repeatability of 2 microns, and a minimum incremental motion of 100 nm.
    This is potentially too coarse.

C-884
~~~~~

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: PI
                  serial_number: 119060508
                  axes: [x, y, z, theta, f]
                  axes_mapping: [1, 2, 3, 4, 5]
                  feedback_alignment: 
                  volts_per_micron: 0.0
                  min: 
                  max: 
                  controllername: C-884
                  stages: L-509.20DG10 L-509.40DG10 L-509.20DG10 M-060.DG M-406.4PD NOSTAGE
                  refmode: FRF FRF FRF FRF FRF FRF
                  port: 
                  baudrate: 
                  timeout: 
              joystick_axes: [x, y, z]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|

E-709
~~~~~

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: PI
                  serial_number: 119060508
                  axes: [x, y, z, theta, f]
                  axes_mapping: [1, 2, 3, 4, 5]
                  feedback_alignment: 
                  volts_per_micron: 0.0
                  min: 
                  max: 
                  controllername: E-709
                  stages: L-509.20DG10 L-509.40DG10 L-509.20DG10 M-060.DG M-406.4PD NOSTAGE
                  refmode: FRF FRF FRF FRF FRF FRF
                  port: 
                  baudrate: 
                  timeout: 
              joystick_axes: [x, y, z]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|

------------------

Thorlabs
--------

KIM001
~~~~~~
**navigate** supports the `KIM001 <https://www.thorlabs.com/thorproduct
.cfm?partnumber=KIM001>`_ controller. However, this device shows significant
hysteresis, and thus we do not recommend it for precise positioning tasks (e.g.,
autofocusing). It serves as a cost-effective solution for manual, user-driven
positioning.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: Thorlabs
                  serial_number: 74000375
                  axes: [f]
                  axes_mapping: [1]
                  feedback_alignment: 
                  volts_per_micron: 0.0
                  min: 
                  max: 
                  controllername:
                  stages: 
                  refmode: 
                  port: 
                  baudrate: 
                  timeout: 
              joystick_axes: [f]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|


KST101
~~~~~~

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: KST101
                  serial_number: 26001318
                  axes: [f]
                  axes_mapping: [1]
                  feedback_alignment:
                  device_units_per_mm: 20000000/9.957067
                  volts_per_micron: 0.0
                  min: 0
                  max: 25
                  controllername:
                  stages: 
                  refmode: 
                  port: 
                  baudrate: 
                  timeout: 
              joystick_axes: [f]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|
--------------

.. _galvo_stage:

Analog-Controlled Galvo/Piezo
-----------------------------

We sometimes control position via a galvo or piezo with no software API.
In this case, we treat a standard galvo mirror or piezo as a stage axis. We control the
"stage" via voltages sent to the galvo or piezo. The ``volts_per_micron`` setting
allows the user to pass an equation that converts position in microns ``X``, which is
passed from the software stage controls, to a voltage. Note that we use
``GalvoNIStage`` whether or not the device is a galvo or a piezo since the logic is
identical. The voltage signal is delivered via the data acquisition card specified in the
``axes_mapping`` entry.

.. note::

    The parameters ``distance_threshold`` and ``settle_duration_ms`` are used to provide
    a settle time for large moves. if the move is larger than the ``distance_threshold``,
    then a wait duration of ``settle_duration_ms`` is used to allow the stage to settle
    before the image is acquired.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: GalvoNIStage
                  serial_number: 001
                  axes: [Z]
                  axes_mapping: [PCI6738/ao6]
                  volts_per_micron: 0.05*x
                  min: 0.0
                  max: 1.0
                  distance_threshold: 5
                  settle_duration_ms: 5
                  controllername:
                  stages:
                  refmode:
                  port:
                  baudrate: 0
              joystick_axes: [f]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|

----------------

Synthetic Stage
---------------
If no stage is present for a particular axis, one must configure the software to use a synthetic
stage. For example, not all microscopes have a theta axis.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            stage:
              hardware:
                -
                  type: synthetic
                  serial_number: 001
                  axes: [x, y, z, theta, f]
                  axes_mapping: [A, B, C, D, E]
                  volts_per_micron: 0.0
                  min: 0.0
                  max: 1.0
                  controllername:
                  stages:
                  refmode:
                  port:
                  baudrate: 0
              joystick_axes: [x, y, z]
              x_min: -10000.0
              x_max: 10000.0
              y_min: -10000.0
              y_max: 10000.0
              z_min: -10000.0
              z_max: 10000.0
              theta_min: 0.0
              theta_max: 360.0
              f_min: -10000.0
              f_max: 10000.0
              x_offset: 0.0
              y_offset: 0.0
              z_offset: 0.0
              theta_offset: 0.0
              f_offset: 0.0
              flip_x: False
              flip_y: False
              flip_z: False
              flip_f: False

|
