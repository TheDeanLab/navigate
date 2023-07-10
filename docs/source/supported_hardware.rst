Supported Hardware
====================

Data Acquisition Card
----------------------------
NI
^^^^^^^^^^
We have used several different NI-based data acquisition cards to run the software.
These include PCIe-6738, PXIe-6259, and PXIe-6733. Prior to installing the card within the computer, first install
the `NI-DAQmx drivers <https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html#464560>`_. Once installed,
connect the PCIe or PXIe-based device to the computer. A functioning system should be recognized by the operating system,
and visible in the Windows Device Manager as a **NI Data Acquisition Device**.

.. tip::

    To find the device pinouts for your NI-based data acquisition card, open up NI MAX, find the card under devices,
    right-click and select 'device pinouts'.

    Important: Should you use the SCB-68A breakout box, do not look at the pinout on the back of the cover.
    This is misleading. You must look at the device pinouts in NI MAX.

The most important aspect is to wire up the triggering properly. The software first calculates all of the analog and digital waveforms, creates the NI tasks, and then queues these waveforms on the data acquisition board.
Upon receipt of a trigger, all of the analog an digital tasks are delivered in parallel. This provides us with deterministic behavior on a per-frame basis, which is necessary for proper ASLM-style acquisitions. It does not
however provide us with deterministic behavior between image frames, and some jitter in timing is anticipated.

Wiring
- Identify the device name in NI MAX, and change it if you would like. Common names are ``Dev1``, ``Dev2``, etc. This name must correspond with the pinouts provided in the configuration file.

- Connect the ``master_trigger_out_line`` to the ``trigger_source`` with a direct wire, commonly ``PXI6259/port0/line1`` and ``/PXI6259/PFI0``

.. note::

    For NI-based cards, port0/line1 is the equivalent of ``P0.1``.
    There are multiple pins for each PFIO, including source, out, gate, etc. You must use the out terminal.

Cameras
----------
Hamamatsu
^^^^^^^^^^^^^^^^^^^^^^
* Insert the USB that came with the camera into the computer and install HCImageLive.
* When prompted with the DCAM-API Setup

    * Intall the Active Silicon Firebird drivers for the FrameGrabber
    * Select ... next to the tools button, and install DCAM tools onto the computer.

* Shutdown the computer and intall the Hamamatsu frame grabber into an apporpriate PCIe-x16 slot on the motherboard.
* Turn on the computer and the camera, and confirm that it is functioning properly in HCImageLive or Excap (one of the DCAM tools installed)
* Connect the `camera_trigger_out_line` to the External Trigger of the Hamamatsu Camera. Commonly, this is done with a
counter port, e.g., ``/PXI6259/ctr0``

Photometrics
^^^^^^^^^^^^^^^^^^^^^^^^
* Download the `PVCAM software <https://www.photometrics.com/support/software-and-drivers>`_ from Photometrics.
The PVCAM SDK is also available form this location.
You will likely have to register and agree to Photometrics terms.
* Perform the Full Installation of the PVCAM software.
* Should a 'Base Device' still show up as unknown in the device manager, you may need to install the
`Broadcom PCI/PCIe Software Development Kit <https://www.broadcom.com/products/pcie-switches-bridges/software-dev-kits`_
* Upon successfully installation, one should be able to acquire images with the manufacturer provided PVCamTest software.


Voicecoil
--------------
Equipment Solutions
^^^^^^^^^^^^^^^^^^^^^

* `SCA814 Linear Servo Controller <https://www.equipsolutions.com/products/linear-servo-controllers/sca814-linear-servo-controller/>`_

    * +/- 2.5 Volt Analog Input

* `LFA-2010 Linear Focus Actuator <https://www.equipsolutions.com/products/linear-focus-actuators/lfa-2010-linear-focus-actuator/>`_

Thorlabs BLINK
^^^^^^^^^^^^^^^^^^^^^
In progress...

Stages
------------------------
ASI
^^^^^^^^^^^^^^^^^
Software designed to acquire data in a continuous stage scanning mode. Rather than using the default SYNC ignal
from the ASI stage to synchronize the start of imaging, we use the encoder output pulsing mode of the ASI stage to
trigger the acquisition of every frame at precise intervals.  Important for multi-channel imaging that is acquired in
the per-stack mode, but less so for perZ-based acquisitions.

FTP-2000 Stage. Whatever you do, don't change the F position. You will your stage.

Sutter
^^^^^^^^^^^^^^^^^
In progress...

Physik Instrumente
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In progress...

Thorlabs
^^^^^
In progress...

Analog Controlled (Galvo/Piezo/etc.)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In progress...

Deformable Mirrors
------------------------
Imagine Optics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In progress...

Filter Wheels
----------------------------
Sutter
^^^^^^^^^^^^^^^^^^^^^^
In progress...

ASI
^^^^^^^^^^^^^^^^^^^^^^
In progress...

Galvanometers
----------------------------
Cambridge Technologies/Novanta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In progress...

ScannerMAX
^^^^^^^^^^^^^^^^^^^^
In progress...


Lasers
----------
Coherent
^^^^^^^^^^^^^^^^^^^^^
In progress...

Omicron
^^^^^^^^^^^^^^^^^^^^^

Shutters
-----------------------------
Thorlabs
^^^^^^^^^^^^
In progress...


Mechanical Zoom
---------------------------------
Dynamixel
^^^^^^^^^^^^
In progress...
