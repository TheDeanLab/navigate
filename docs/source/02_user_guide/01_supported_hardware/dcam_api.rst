.. _dcam:

=================
Hamamatsu Drivers
=================

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
