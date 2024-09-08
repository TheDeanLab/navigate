.. _pvcam:

====================
Photometrics Drivers
====================

* Download the `PVCAM software <https://www.photometrics.com/support/software-and-drivers>`_
  from Photometrics. The PVCAM SDK is also available form this location. You will
  likely have to register and agree to Photometrics terms.
* Perform the Full Installation of the PVCAM software.
* Should a "Base Device" still show up as unknown in the Windows Device Manager, you
  may need to install the `Broadcom PCI/PCIe Software Development Kit <https://www.broadcom.com/products/pcie-switches-retimers/software-dev-kits>`_
* Upon successful installation, one should be able to acquire images with the
  manufacturer-provided PVCamTest software.

.. Note::

    A static version of the Photometrics API is provided with this software. It is located
    in in srcs/model/devices/APIs/photo_metrics/PyVCAM-master. To install this API, go to this
    folder in the command line and from within your **navigate** environment, run
    ``python setup.py install``.
