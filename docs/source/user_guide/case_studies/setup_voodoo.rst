.. _setup_aslm:

==================================================
Setting up an Axially Swept Light-Sheet Microscope
==================================================

Important points
================
The key to properly setting up the navigate software is to sequentially enable select
devices, and troubleshoot each one independently. By carefully and methodically
adding devices, and checking that they are functional, one can be confident that the
entire system is working as intended. In this example, we will be using a Hamamatsu
Flash 4.0 camera. However, you may also use another Hamamatsu sCMOS model, or a
Photometrics camera, as long as the drivers are installed and the camera is
recognized by the computer. The microscope will operate in a sample scanning format
for volumetric image acquisition.

-------------

First steps
============

#. Launch the software in synthetic hardware mode. This requires that the conda
   environment has been established, and that the software has been installed. Once the
   conda environment has been activated, the software can be launched by typing
   ``navigate -sh`` in the terminal.

#. Once the software has been launched, the GUI will appear. Open the folder
   containing the configuration files by selecting to the menu :menuselection:`File -->
   Open Configuration Files`. This will open the ``.navigate`` folder in the file
   explorer, which is where local configuration files are stored.

#. Open the ``configuration.yaml`` file in your preferred integrated development
   environment (e.g., PyCharm, VSCode, etc.).

#. For every device in the ``hardware`` and ``microscopes`` sections of the
   ``configuration.yaml`` file, you will need to change the type to ``synthetic``.
   For convenience, we provide a ``synthetic_configuration.yaml`` file in
   ``navigate/src/navigate/config`` that can be  used to replace the
   ``configuration.yaml`` file that already has synthetic for each  device. You will
   need to replace the ``configuration.yaml`` file that is located in the ``.navigate``
   folder with the ``synthetic_configuration.yaml`` file.

#. Restart the software, but this time launch it in a standard operating mode by
   typing ``navigate`` in the terminal. This confirms that the base configuration file is
   functional. If any problems are encountered, please submit a ticket on
   `GitHub <https://github.com/TheDeanLab/navigate>`_ under the "Issues" tab.

-------------

Sequentially adding devices
===========================

Data Acquisition Card
---------------------

#. We will now begin sequentially adding non-synthetic devices to the configuration
   file. The first device to add is the NI data acquisition card. Of course, the data
   acquisition card's drivers must be `installed <https://www.ni
   .com/en/support/downloads/drivers/download.ni-daq-mx.html#494676>`_ and functioning.
   To confirm that it is functioning, it is best to use the `NI MAX` software and
   evaluate the card's functionality with an oscilloscope.

#. In the ``hardware`` and ``microscopes`` sections of the ``configuration.yaml`` file,
   change the ``type`` to ``NI``. You will also need to hard-wire the
   ``master_trigger_out_line`` to the ``trigger_source``. The identity of these pins
   can be found in the NI MAX software by right-clicking on the device and selecting
   :guilabel:`Device Pinouts`. You will also need to make sure that the identity of the
   pinouts is correct in the ``configuration.yaml`` file. Most commonly, NI cards
   default to a device name such as "Dev1". You can change this name in NI MAX, or
   leave it as is, but whatever you do it has to match the name in the
   ``configuration.yaml`` file (e.g., ``PXI6259/port0/line1`` if the name of the device
   is "PXI6259" and the pinout is "port0/line1").

#. Open the ``navigate`` software in the standard operating mode, select the
   "Continuous Scan" mode, and press :guilabel:`Acquire`. If the software is operating
   as expected, it should display a synthetically generated image of noise. If it does
   not, double-check the configuration file and make sure that the
   ``master_trigger_out_line`` is connected to the ``trigger_source``.

----------

Camera
------

#. Next, we will add the camera. The camera must be connected to the computer via a USB
   or the dedicated frame-grabber cable. The camera drivers must also be installed. The
   camera drivers can be found on the `DCAM-API Website <https://dcam-api.com>`_.

#. Update the camera type to ``HamamatsuOrca`` and input the correct serial number,
   which can be found on the camera label or through the DCAMConfigurator or HCImage.
   You will also need to connect the ``camera_trigger_out_line`` on the data
   acquisition card to the BNC port labeled "Ext. Trig." on the back of the camera.

#. Restart the software and begin an acquisition in the "Continuous Scan" mode. The
   camera should now be delivering frames to the software.

----------

Filter Wheel
------------

#. Set up the Filter Wheel. First, identify the comport via the device manager
   on Windows. Change the ``filter_wheel`` type to ``SutterFilterWheel`` or equivalent
   in the ``hardware`` and ``microscopes`` sections of the configuration file, and
   provide the necessary information for that filter wheel device (e.g., ``baudrate``).
   At this point, you can also name each filter if desired under the
   ``available_filters`` section.

#. Restart the software and select multiple channels in the
   :guilabel:`Channel Settings` tab, each with different filters. Run the software in
   "Continuous Scan" mode again and ensure that the filter wheel is changing filters
   between each acquisition.

----------

Lasers
------

#. Set up the lasers. Ideally, the lasers will operate in a mixed modulation mode,
   which requires that the NI card provides both analog and digital signals to each
   laser. This allows blanking of the laser, as well as control of its intensity. Open
   the control software for the lasers, and configure them in a mixed modulation mode.
   Next, connect the analog output of the NI card to the analog input of the laser.
   Finally, connect the digital output of the NI card to the digital input of the laser.
   A common port for the analog and digital outputs are ``PXI6733/ao0`` and
   ``PXI6733/port0/line2``, respectively.

#. Configure the lasers in the ``hardware`` and ``microscopes`` sections of the
   configuration to type ``NI``. Here, you can specify the wavelength of each laser, as
   well as the minimum and maximum volts to deliver to the laser in both the analog
   (``power``) and digital (``onoff``) sections.

----------

Remote focusing unit
--------------------

#. Configure the Voice Coil. Most voice coils only require an analog signal to
   control, which can be delivered via the type ``NI`` in the ``hardware`` and
   ``microscopes``. However, some voice coils must be configured to accept an
   analog signal upon each power cycle (e.g., ``EquipmentSolutions``). In this
   case, you will also need to specify the COM port.

----------

Galvos
------

#. Set up the galvos. Galvos can be used for a wide variety of tasks, including
   shadow reduction, digitally scanned light-sheet formation, and also for stepping the
   beam in z during the acquisition of a z-stack. If the galvo will be used for a
   z-stack, it should be configured in the ``stage`` section. All other galvos are
   placed in ``galvo`` section. For a sample-scanning ASLM, we use a resonant galvo
   to perform shadow reduction.

----------

Stages
------

#. Install and configure the Stages. You will need to specify stages for the ``x``,
   ``y``, ``z``, ``theta``, and ``f`` axes. If you do not need one of these stages,
   it should remain specified as a ``SyntheticStage``. It is also important to make
   sure that you map the stage coordinates to the software coordinates. For example,
   with the Sutter MP285, the vertical movement of the stage is its z axis. However,
   for light-sheet microscopes that are laid out horizontally, this axis is the x axis.
   Thus, we must map the hardware z-axis to the software x-axis. This is done with the
   ``axes`` and ``axes_mapping`` entries, which for the example provided, would be as
   follows:

   .. code-block:: yaml

        axes: [x] # software axes
        axes_mapping: [z] #hardware axes

   Importantly, any stage you designate as ``z`` will be used for acquisition of a z-stack.
