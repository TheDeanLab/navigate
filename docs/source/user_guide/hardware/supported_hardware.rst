==================
Supported Hardware
==================

Data Acquisition Card
=====================

Data acquisition cards deliver and receive analog and digital signals.
To acquire an image, the software calculates all of the analog and digital waveforms and
queues these waveforms on the data acquisition card. Upon receipt of a trigger (either from the software itself,
or an external piece of hardware), all
of the analog and digital signals are delivered in parallel. This provides
deterministic behavior on a per-frame basis, which is necessary for proper acquisition of light-sheet data.
It does not however provide us with deterministic behavior between image
frames, and some jitter in timing is anticipated.

------------------

.. _hardware_ni:

National Instruments (NI)
-------------------------
In principle, most NI-based data acquisition cards should work with the software, so long
as there are a sufficient number of analog and digital ports, and the sampling rate (typically 100 kHz)
is high enough per port.

Prior to installing the card within
the computer, first install the `NI-DAQmx drivers <https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html#464560>`_.
Once installed, connect the PCIe or PXIe-based device to the computer. A functioning
system should be recognized by the operating system, and visible in the Windows Device
Manager as a **NI Data Acquisition Device**.


.. tip::

    **The most important aspect is to wire up the breakout box properly.**

    To find the device pin outs for your NI-based data acquisition card, open NI
    MAX, find the card under devices, right-click and select "device pinouts".

    Important: Should you use the SCB-68A breakout box, do not look at the pinout on
    the back of the cover. This is misleading. You must look at the device pinouts in
    NI MAX.

Wiring
^^^^^^

- Identify the device name in NI MAX, and change it if you would like. Common names are
  ``Dev1``, ``Dev2``, etc. This name must correspond with the pinouts provided in the
  configuration file.

- Connect the ``master_trigger_out_line`` to the ``trigger_source`` with a direct wire,
  commonly ``PXI6259/port0/line1`` and ``/PXI6259/PFI0``. In this example, the default name
  for the device (e.g., ``Dev1``) has been changed to ``PXI6259``.

- Connect the ``camera_trigger_out_line`` to the ``Ext. Trigger`` on the camera using
  the ``CTR0Out`` pin.

- These values must precisely match those in the configuration file. An example is provided below:


.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        daq:
          type: NI

      microscopes:
        microscope_name:
          daq:
            hardware:
              name: daq
              type: NI
            sample_rate: 100000
            sweep_time: 0.2
            master_trigger_out_line: PCI6738/port0/line1
            camera_trigger_out_line: /PCI6738/ctr0
            trigger_source: /PCI6738/PFI0
            laser_port_switcher: PCI6738/port0/line0
            laser_switch_state: False

|

.. note::

    For NI-based cards, ``port0/line1`` is the equivalent of ``P0.1``.
    There are multiple pins for each PFIO, including source, out, gate, etc. You must
    use the out terminal.

The software has been tested with the following NI-based cards:

PCIe/PXIe-6738
^^^^^^^^^^^^^^^^^
The PCIe-6738 can only create one software-timed analog task for every four channels.
As such, the lasers much be attached to analog output ports outside of the banks (shown as solid lines in the device pinout) used
by the galvo/remote focus units. For example, if you use ao0, ao2, and ao6 for the
remote focus, galvo, and galvo stage, the lasers should be connected to ao8, ao9, and
ao10. In such a configuration, they will not compete with the other analog output
ports. Since only one task will be created created on the ao8, ao9, ao10 bank at a time
(only one laser is on at a time), only one laser can be on at a time. If we wanted to
turn lasers on simultaneously, we could distribute the lasers across independent banks
(e.g. ao8, ao14, ao19).

.. collapse:: Device Pinout

    .. image:: images/6738_pinout.png

|

PCIe/PXIe-6259
^^^^^^^^^^^^^^^

The PXI-6259 can create one software-timed analog task per channel. As such, the
galvo/remote focus/lasers can be attached to any of the analog output ports. The 6259 has
two connectors, and it is important to make sure that the analog and digital ports that you
are using are connected to the correct connector. For example, if you are using ``ao0``, this is
located on ``connector 0``.

.. collapse:: Device Pinout

    .. image:: images/6259_pinout.png

|

PCIe/PXIe-6723
^^^^^^^^^^^^^^^

The PXI-6723 can also create one software-timed analog task per channel. As such, the analog
outputs can be wired up as is most convenient.

.. collapse:: Device Pinout

    .. image:: images/6723_pinout.png

Synthetic Data Acquisition Card
-------------------------------
If no data acquisition card is present, one must configure the software to use a synthetic
data acquisition card.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        daq:
          type: SyntheticDAQ

      microscopes:
        microscope_name:
          daq:
            hardware:
              name: daq
              type: SyntheticDAQ
            sample_rate: 100000
            sweep_time: 0.2
            master_trigger_out_line: PCI6738/port0/line1
            camera_trigger_out_line: /PCI6738/ctr0
            trigger_source: /PCI6738/PFI0
            laser_port_switcher: PCI6738/port0/line0
            laser_switch_state: False

|

---------

.. _camera_configuration:
Cameras
=======

The software supports camera-based acquisition. It can run both normal and rolling
shutter modes of contemporary scientific CMOS cameras.

Hamamatsu ORCA-Flash4.0 V3/Fusion
---------------------------------

* Insert the USB that came with the camera into the computer and install HCImageLive. Alternatively,
  download DCAM-API. The software can be found `here <https://dcam-api.com>`_.
* When prompted with the DCAM-API Setup

    * If you are going to use the Frame Grabber, install the Active Silicon Firebird drivers.
    * Select ... next to the tools button, and install DCAM tools onto the computer.

* Shutdown the computer and install the Hamamatsu frame grabber into an appropriate
  PCIe-x16 slot on the motherboard.
* Turn on the computer and the camera, and confirm that it is functioning properly in
  HCImageLive or Excap (one of the DCAM tools installed).
* Connect the `camera_trigger_out_line` to the External Trigger of the Hamamatsu
  Camera. Commonly, this is done with a counter port, e.g., ``/PXI6259/ctr0``

More about the ORCA-Flash 4.0 v3 and ORCA-Fusion can be found `here <https://www.hamamatsu.com/us/en/product/cameras/cmos-cameras/C13440-20CU.html>`_ and
`here <https://www.hamamatsu.com/us/en/product/cameras/cmos-cameras/C14440-20UP.html>`_, respectively.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        camera:
          -
            type: HamamatsuOrca
            serial_number: 302153

      microscopes:
        microscope_name:
          camera:
            hardware:
              name: camera
              type: HamamatsuOrca
              serial_number: 302153
            x_pixels: 2048.0
            y_pixels: 2048.0
            flip_x: True
            flip_y: False
            pixel_size_in_microns: 6.5
            subsampling: [1, 2, 4]
            sensor_mode: Normal
            readout_direction: Top-to-Bottom
            lightsheet_rolling_shutter_width: 608
            defect_correct_mode: 1.0
            binning: 1x1
            readout_speed: 2.0
            trigger_active: 1.0
            trigger_mode: 1.0
            trigger_polarity: 2.0
            trigger_source: 2.0
            exposure_time: 20
            delay_percent: 20
            pulse_percent: 1
            line_interval: 0.000075
            display_acquisition_subsampling: 4
            average_frame_rate: 4.969
            frames_to_average: 1
            exposure_time_range:
              min: 1
              max: 1000
              step: 1
            x_pixels_step: 4
            y_pixels_step: 4
            x_pixels_min: 4
            y_pixels_min: 4

|

Hamamatsu ORCA-Lightning
------------------------

The Hamamatsu ORCA-Lightning has a slightly different class than the Flash/Fusion as it
reads out 4 rows at a time rather than 1 in rolling shutter mode.
Learn more `here <https://www.hamamatsu.com/us/en/product/cameras/cmos-cameras/C14120-20P.html>`_.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        camera:
          -
            type:  HamamatsuOrcaLightning
            serial_number: 000035

      microscopes:
        microscope_name:
          camera:
            hardware:
              name: camera
              type: HamamatsuOrcaLightning
              serial_number: 000035
            x_pixels: 4608.0
            y_pixels: 2592.0
            pixel_size_in_microns: 5.5
            subsampling: [1, 2, 4]
            sensor_mode: Normal
            readout_direction: Bottom-to-Top
            lightsheet_rolling_shutter_width: 608
            defect_correct_mode: 2.0
            binning: 1x1
            readout_speed: 0x7FFFFFFF
            trigger_active: 1.0
            trigger_mode: 1.0
            trigger_polarity: 2.0
            trigger_source: 2.0
            exposure_time: 20
            delay_percent: 8
            pulse_percent: 1
            line_interval: 0.000075
            display_acquisition_subsampling: 4
            average_frame_rate: 4.969
            frames_to_average: 1
            exposure_time_range:
              min: 1
              max: 1000
              step: 1

|


Hamamatsu ORCA-Fire
-------------------

The Hamamatsu ORCA-Fire is one of the latest releases from Hamamatsu. It is a
scientific CMOS camera that offers large 10.5 MPix sensor and greater diversity
of rolling shutter readout modes. Learn more `here <https://www.hamamatsu.com/us/en/product/cameras/cmos-cameras/C16240-20UP.html>`_.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        camera:
          -
            type:  HamamatsuOrcaFire
            serial_number: 000035

      microscopes:
        microscope_name:
          camera:
            hardware:
              name: camera
              type: HamamatsuOrcaFire
              serial_number: 000035
            x_pixels: 4432.0
            y_pixels: 2368.0
            pixel_size_in_microns: 4.6
            subsampling: [1, 2, 4]
            sensor_mode: Normal
            readout_direction: Bottom-to-Top
            lightsheet_rolling_shutter_width: 608
            defect_correct_mode: 2.0
            binning: 1x1
            readout_speed: 0x7FFFFFFF
            trigger_active: 1.0
            trigger_mode: 1.0
            trigger_polarity: 2.0
            trigger_source: 2.0
            exposure_time: 20
            delay_percent: 8
            pulse_percent: 1
            line_interval: 0.000075
            display_acquisition_subsampling: 4
            average_frame_rate: 4.969
            frames_to_average: 1
            exposure_time_range:
              min: 1
              max: 1000
              step: 1

|

Photometrics Iris 15
--------------------

* Download the `PVCAM software <https://www.photometrics.com/support/software-and-drivers>`_
  from Photometrics. The PVCAM SDK is also available form this location. You will
  likely have to register and agree to Photometrics terms.
* Perform the Full Installation of the PVCAM software.
* Should a "Base Device" still show up as unknown in the Windows Device Manager, you
  may need to install the `Broadcom PCI/PCIe Software Development Kit <https://www.broadcom.com/products/pcie-switches-bridges/software-dev-kits>`_
* Upon successful installation, one should be able to acquire images with the
  manufacturer-provided PVCamTest software.


.. collapse:: Configuration File

    .. code-block:: yaml

      camera:
        type: Photometrics
        camera_connection: PMPCIECam00
        serial_number: 1

      camera:
          hardware:
            name: camera
            type: Photometrics
            serial_number: 1
          x_pixels: 5056.0
          y_pixels: 2960.0
          pixel_size_in_microns: 4.25
          subsampling: [1, 2, 4]
          sensor_mode: Normal
          readout_direction: Bottom-to-Top
          lightsheet_rolling_shutter_width: 608
          defect_correct_mode: 2.0
          binning: 1x1
          readout_speed: 0x7FFFFFFF
          trigger_active: 1.0
          trigger_mode: 1.0
          trigger_polarity: 2.0
          trigger_source: 2.0
          exposure_time: 20
          delay_percent: 25
          pulse_percent: 1
          line_interval: 0.000075
          display_acquisition_subsampling: 4
          average_frame_rate: 4.969
          frames_to_average: 1
          exposure_time_range:
            min: 1
            max: 1000
            step: 1

|

Synthetic Camera
----------------

The synthetic camera simulates noise images from an sCMOS camera. If no camera is present,
the synthetic camera class must be used.

.. collapse:: Configuration File

    .. code-block:: yaml

      camera:
        type: SyntheticCamera
        serial_number: 12345

       microscopes:
        microscope_name:
          camera:
            hardware:
              name: camera
              type: SyntheticCamera
              serial_number: 12345
            x_pixels: 2048.0
            y_pixels: 2048.0
            flip_x: True
            flip_y: False
            pixel_size_in_microns: 6.5
            subsampling: [1, 2, 4]
            sensor_mode: Normal
            readout_direction: Top-to-Bottom
            lightsheet_rolling_shutter_width: 608
            defect_correct_mode: 1.0
            binning: 1x1
            readout_speed: 2.0
            trigger_active: 1.0
            trigger_mode: 1.0
            trigger_polarity: 2.0
            trigger_source: 2.0
            exposure_time: 20
            delay_percent: 20
            pulse_percent: 1
            line_interval: 0.000075
            display_acquisition_subsampling: 4
            average_frame_rate: 4.969
            frames_to_average: 1
            exposure_time_range:
              min: 1
              max: 1000
              step: 1
            x_pixels_step: 4
            y_pixels_step: 4
            x_pixels_min: 4
            y_pixels_min: 4

|


---------


Remote Focusing Devices
=======================

Voice coils, also known as linear actuators, play a crucial role in implementing
aberration-free remote focusing in navigate. These electromagnetic actuators are used
to control the axial position of the light-sheet and the sample relative to the
microscope objective lens. By precisely adjusting the axial position, the focal plane
can be shifted without moving the objective lens, thus enabling remote focusing. Focus tunable lenses
serve as an alternative to voice coils owing to their simple operation and high bandwidth. Tunable lenses axially scan
a beam by introducing defocus into the optical train. Nonetheless, they do not provide the
higher-order correction provided by voice coils in an aberration-free remote focusing system.

Equipment Solutions
-------------------

Configuration of the device can be variable. Many voice coils we have received require
establishing serial communication with the device to explicitly place it in an analog
control mode. In this case, the comport must be specified properly in the configuration
file.

More recently, Equipment Solutions has begun delivering devices that
automatically initialize in an analog control mode, and thus no longer need the
serial communication to be established. For these devices, we recommend using the analog
control mode described in the next section.

The `LFA-2010 Linear Focus Actuator <https://www.equipsolutions.com/products/linear-focus-actuators/lfa-2010-linear-focus-actuator/>`_
is controlled with a `SCA814 Linear Servo Controller <https://www.equipsolutions.com/products/linear-servo-controllers/sca814-linear-servo-controller/>`_,
which accepts a +/- 2.5 Volt analog signal. The minimum and maximum voltages can be set
in the configuration file to prevent the device from receiving a voltage outside of its
operating range.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          remote_focus_device:
            hardware:
              name: remote_focus
              type: EquipmentSolutions
              channel: PCI6738/ao2
              comport: COM7
              min: -2.5
              max: 2.5
            delay_percent: 7.5
            ramp_rising_percent: 85
            ramp_falling_percent: 5.0
            amplitude: 0.7
            offset: 2.3
            smoothing: 0.0

|

Analog Controlled Voice Coils and Tunable Lenses
------------------------------------------------

In principle, this hardware type can support any analog-controlled voice coil or tunable lens.
The `BLINK <https://www.thorlabs.com/thorproduct.cfm?partnumber=BLINK>`_ and the
`Optotune Focus Tunable Lens <https://www.optotune.com/tunable-lenses>`_ are
controlled with an analog signal from the DAQ. The BLINK is a voice coil that is
pneumatically actuated voice coil. it is recommended that you specify the min and max voltages
that are compatible with your device to prevent the device from receiving a voltage outside of its
operating range.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          remote_focus_device:
            hardware:
              name: remote_focus
              type: NI
              channel: PCI6738/ao2
              comport: COM7
              min: -2.5
              max: 2.5
            delay_percent: 7.5
            ramp_rising_percent: 85
            ramp_falling_percent: 5.0
            amplitude: 0.7
            offset: 2.3
            smoothing: 0.0

|

Synthetic Remote Focus Device
-----------------------------
If no remote focus device is present, one must configure the software to use a synthetic
remote focus device.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          remote_focus_device:
            hardware:
              name: remote_focus
              type: SyntheticRemoteFocus
              channel: PCI6738/ao2
              comport: COM7
              min: -2.5
              max: 2.5
            delay_percent: 7.5
            ramp_rising_percent: 85
            ramp_falling_percent: 5.0
            amplitude: 0.7
            offset: 2.3
            smoothing: 0.0

|

---------


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

ASI Tiger Controller
--------------------

The ASI `Tiger Controller <https://www.asiimaging.com/controllers/tiger-controller/>`_. is
a multi-purpose controller for ASI stages, filter wheels, dichroic sliders,
and more. We communicate with Tiger Controllers via a serial port. It is recommended that you
first establish communication with the device using `ASI provided software <https://asiimaging.com/docs/products/tiger>`_.
For stages in particular, there is a ``feedback_alignment`` configuration option option
corresponds to the `Tiger Controller AA Command <https://asiimaging.com/docs/commands/aalign>`_.

.. tip::
    If you are using the FTP-2000 stage, do not change the F stage axis. This
    will differentially drive the two vertical posts, causing them to torque and
    potentially damage one another.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        stage:
          type: ASI
          serial_number: 123456789
          port: COM8
          baudrate: 115200

      microscopes:
        microscope:
          stage:
            hardware:
              name: stage
              type: ASI
              serial_number: 123456789
              axes: [x, y, z, f]
              axes_mapping: [M, Y, X, Z]
              feedback_alignment: [90, 90, 90, 90]

|

Sutter MP-285
-------------

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

      hardware:
        stage:
        -
          type: MP285
          port: COM2
          timeout: 0.25
          baudrate: 9600
          serial_number: 0000
          stages: None

      microscopes:
        microscope_name:
          stage:
            hardware:
              name: stage1
              type: MP285
              serial_number: 0000
              axes: [y, x, f]
              axes_mapping: [z, y, x]
              volts_per_micron: None
              axes_channels: None
              max: 25000
              min: 0

|

Physik Instrumente
------------------

These stages are controlled by `PI <https://www.pi-usa.us/en/>`_'s own
`Python code <https://pypi.org/project/PIPython/>`_ and are quite stable. They
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

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        stage:
          -
            type: PI
            controllername: C-884
            stages: L-509.20DG10 L-509.40DG10 L-509.20DG10 M-060.DG M-406.4PD NOSTAGE
            refmode: FRF FRF FRF FRF FRF FRF
            serial_number: 119060508
          -
      microscopes:
        microscope_name:
          stage:
            hardware:
              name: stage
              type: PI
              serial_number: 119060508
              axes: [x, y, z, theta, f]
            y_unload_position: 10000
            y_load_position: 90000

            startfocus: 75000
            x_max: 100000
            x_min: -100000
            y_max: 100000
            y_min: -100000
            z_max: 100000
            z_min: -100000
            f_max: 100000
            f_min: 0
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

|

Thorlabs
--------

We currently support the `KIM001 <https://www.thorlabs.com/thorproduct.cfm?partnumber=KIM001>`_
controller. Importantly, this device shows significant hysterisis, and thus we do not recommend
it for precise positioning tasks (e.g., autofocusing). It serves as a cost-effective solution
for manual, user-driven positioning.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        stage:
          -
            type: Thorlabs
            serial_number: 74000375

      microscopes:
        microscope_name:
          stage:
              hardware:
                -
                  name: stage
                  type: Thorlabs
                  serial_number: 74000375
                  axes: [f]
                  axes_mapping: [1]
                  volts_per_micron: None
                  axes_channels: None
                  max: None
                  min: None

|

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

      hardware:
        stage:
        -
          type: GalvoNIStage
          port: COM9999
          timeout: 0.25
          baudrate: 9600
          serial_number: 0000
          stages: None
          distance_threshold: 20
          settle_duration_ms: 5

      microscopes:
        microscope_name:
          stage:
            hardware:
                name: stage3
                type: GalvoNIStage
                serial_number: 0000
                axes: [z]
                axes_mapping: [PCI6738/ao6]
                volts_per_micron: 0.05*x
                max: 10
                min: 0
                distance_threshold: 5
                settle_duration_ms: 5

|


Synthetic Stage
---------------
If no stage is present for a particular axis, one must configure the software to use a synthetic
stage. For example, not all microscopes have a theta axis.


.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        stage:
          -
            type: SyntheticStage
            serial_number: 74000375

      microscopes:
        microscope_name:
          stage:
              hardware:
                -
                  name: stage
                  type: SyntheticStage
                  serial_number: 74000375
                  axes: [theta]
                  axes_mapping: [purple]
                  volts_per_micron: None
                  axes_channels: None
                  max: None
                  min: None

|



---------


Filter Wheels
=============

Filter wheels can be used in both illumination and detection paths. Dichroic
turrets are controlled via the same code as filter wheels. The user is expected to
change the names of available filters to match what is in the filter wheel or turret.

Sutter
------
We typically communicate with Sutter Lambda 10-3 controllers via serial port. It is
recommended that you first establish communication with the device using manufacturer
provided software. Alternatively, one can use MicroManager. For some filter wheel types,
the filter_wheel_delay is calculated according to the size of the move and model of the
filter wheel. For other filter wheel types, the filter_wheel_delay is a fixed value, which is specified as
the ``filter_wheel_delay`` entry in the configuration file. The number of filter wheels
connected to the controller is specified as ``wheel_number`` in the configuration file.
Currently, both wheels are moved to the same position, but future implementations will
enable control of both filter wheels independently.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        filter_wheel:
          type: SutterFilterWheel
          port: COM10
          baudrate: 9600
          number_of_wheels: 1

      microscopes:
        microscope_name:
          filter_wheel:
          hardware:
            name: filter_wheel
            type: SutterFilterWheel
            wheel_number: 1
          filter_wheel_delay: .030
          available_filters:
            Empty-1: 0
            525-30: 1
            600-52: 2
            670-30: 3
            647-LP: 4
            Empty-2: 5
            Empty-3: 6
            Empty-4: 7


|

ASI
---
The ASI filter wheel is controlled by the ASI Tiger Controller. Thus, you should provide the same
``comport`` entry as you did for the stage. A single communication instance is used for both the stage and filter wheel.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        filter_wheel:
          type: ASI
          port: COM10
          baudrate: 115200
          number_of_wheels: 1

      microscopes:
        microscope_name:
          filter_wheel:
            hardware:
              name: filter_wheel
              type: ASI
              wheel_number: 1
            filter_wheel_delay: .030
            available_filters:
              BLU - FF01-442/42-32: 0
              GFP - FF01-515/30-32: 1
              RFP - FF01-595/31-32: 2
              Far-Red - FF01-670/30-32: 3
              Blocked1: 4
              Empty: 5
              Blocked3: 6
              Blocked4: 7
              Blocked5: 8
              Blocked6: 9

|

Synthetic Filter Wheel
----------------------
If no filter wheel is present, one must configure the software to use a synthetic
filter wheel.


.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        filter_wheel:
          type: SyntheticFilterWheel
          port: COM10
          baudrate: 115200
          number_of_wheels: 1

      microscopes:
        microscope_name:
          filter_wheel:
            hardware:
              name: filter_wheel
              type: SyntheticFilterWheel
              wheel_number: 1
            filter_wheel_delay: .030
            available_filters:
              BLU - FF01-442/42-32: 0
              GFP - FF01-515/30-32: 1
              RFP - FF01-595/31-32: 2
              Far-Red - FF01-670/30-32: 3
              Blocked1: 4
              Empty: 5
              Blocked3: 6
              Blocked4: 7
              Blocked5: 8
              Blocked6: 9

|

---------


Galvanometers
=============

Galvo mirrors are used for fast scanning, shadow reduction, and occasionally as stages
(see :ref:`Analog-Controlled Galvo/Piezo <galvo_stage>`).

Analog-Controlled Galvo
-----------------------

Multiple types of galvanometers have been used, including Cambridge
Technologies/Novanta, Thorlabs, and ScannerMAX Each of these devices
are externally controlled via analog signals delivered from a data
acquisition card.

.. collapse:: Configuration File

    .. code-block:: yaml

        microscopes:
          microscope_name:
            galvo:
              -
                hardware:
                  name: daq
                  type: NI
                  channel: PCI6738/ao0
                  min: -5
                  max: 5
                waveform: sawtooth
                frequency: 99.9
                amplitude: 2.5
                offset: 0.5
                duty_cycle: 50
                phase: 1.57079

|


Synthetic Galvo
---------------
If no galvo is present, one must configure the software to use a synthetic
galvo.

.. collapse:: Configuration File

    .. code-block:: yaml

        microscopes:
          microscope_name:
            galvo:
              -
                hardware:
                  name: daq
                  type: SynthticGalvo
                  channel: PCI6738/ao0
                  min: -5
                  max: 5
                waveform: sawtooth
                frequency: 99.9
                amplitude: 2.5
                offset: 0.5
                duty_cycle: 50
                phase: 1.57079

|



Lasers
======
We currently support laser control via voltage signals. In the near-future, we will consider implementing
laser control via serial communication for power control, but digital modulation will still be controlled via
voltage signals.

Omicron LightHUB Ultra
----------------------

.. note::
    Omicron laser source includes both Coherent- and LuxX lasers, which vary
    according to wavelength. LuxX lasers should be operated in an ACC operating
    mode with the analog modulation option enabled. The Coherent Obis lasers should be
    set in the mixed modulation mode.

Coherent Obis
-------------

.. note::
    Coherent Obis lasers should be set in the mixed modulation mode. It is not uncommon
    for the slew rate from the data acquisition card to be insufficient to drive the modulation
    of the laser if the laser is set to an analog modulation mode.

Analog/Digital-Controlled Lasers
--------------------------------

Most lasers are controlled externally via mixed analog and digital modulation.
The ``onoff`` entry is for digital modulation. The ``power`` entry is for analog
modulation.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          lasers:
            - wavelength: 488
              onoff:
                hardware:
                  name: daq
                  type: NI
                  channel: PCI6738/port1/line5
                  min: 0
                  max: 5
              power:
                hardware:
                  name: daq
                  type: NI
                  channel: PCI6738/ao8
                  min: 0
                  max: 5
              type: Obis
              index: 0
              delay_percent: 10
              pulse_percent: 87
            - wavelength: 561...

|


---------


Shutters
========

Shutters automatically open at the start of acquisition and close upon finish.

Analog/Digital-Controlled Shutters
----------------------------------

Thorlabs shutters are controlled via a digital on off voltage.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          shutter:
            hardware:
              name: daq
              type: NI
              channel: PXI6259/port0/line0
              min: 0
              max: 5

|

Synthetic Shutter
-----------------
If no shutter is present, one must configure the software to use a synthetic
shutter.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        shutter:
          hardware:
            name: daq
            type: synthetic
            channel: PCIE6738/port0/line0
            min: 0
            max: 5

|


---------


Mechanical Zoom
===============

Zoom devices control the magnification of the microscope. If such control is not
needed, the software expects a :ref:`Synthetic Zoom <synthetic_zoom>` to provide
the fixed magnification and the effective pixel size of the microscope.

Dynamixel Zoom
--------------

This software supports the
`Dynamixel Smart Actuator <https://www.dynamixel.com/>`_.

.. note::

    The ``positions`` specify the voltage of the actuator at different zoom positions.
    The ``stage_positions`` account for focal shifts in between the different zoom values
    (the MVXPLAPO does not have a consistent focal plane). These may change depending on
    the immersion media. Here it is specified for a ``BABB`` (Benzyl Alcohol Benzyl
    Benzoate) immersion media.  The ``pixel_size`` specifies the effective pixel size of
    the system at each zoom.

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        zoom:
          type: DynamixelZoom
          servo_id: 1
          port: COM18
          baudrate: 1000000

      microscopes:
        microscope_name:
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

|

.. _synthetic_zoom:

Synthetic Zoom
--------------

.. collapse:: Configuration File

    .. code-block:: yaml

      hardware:
        zoom:
          type: synthetic
          servo_id: 1
          port: COM18
          baudrate: 1000000

      microscopes:
        microscope_name:
          zoom:
            hardware:
              name: zoom
              type: synthetic
              servo_id: 1
            position:
              36X: 0
            pixel_size:
              36X: 0.180
            stage_positions:
              BABB:
                f:
                  36X: 0

|


---------


Deformable Mirrors
==================

Imagine Optic
-------------

We currently have support for a
`Mirao 52E <https://www.imagine-optic.com/products/deformable-mirror-mirao-52e/>`_.
The ``flat_path`` provides a path to a system correction ``.wcs`` file, an Imagine
Optic proprietary file that stores actuator voltages and corresponding Zernike
coefficients.

.. collapse:: Configuration File

    .. code-block:: yaml

      mirror:
        type: ImagineOpticsMirror

      mirror:
          hardware:
            name: mirror
            type: ImagineOpticsMirror
            flat_path: D:\WaveKitX64\MirrorFiles\BeadsCoverslip_20231212.wcs
          n_modes: 32


|

Synthetic Mirror
----------------
It is not necessary to have a deformable mirror to run the software. If no deformable
mirror is present, but one wants to evaluate the deformable mirror correction features,
one must configure the software to use a synthetic deformable mirror.

.. collapse:: Configuration File

    .. code-block:: yaml

      mirror:
        type: SyntheticMirror

      mirror:
          hardware:
            name: mirror
            type: ImagineOpticsMirror
            flat_path: D:\WaveKitX64\MirrorFiles\BeadsCoverslip_20231212.wcs
          n_modes: 32


|
