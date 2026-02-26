.. _pvcam:

====================
Photometrics Drivers
====================

* Download the `PVCAM software <https://www.teledynevisionsolutions.com/company/about-teledyne-vision-solutions/teledyne-photometrics/>`_ from Photometrics. The PVCAM SDK is also available from this location. You will likely have to register and agree to Photometrics terms.
* Perform the Full Installation of the PVCAM software.
* Should a "Base Device" still show up as unknown in the Windows Device Manager, you may need to install the `Broadcom PCI/PCIe Software Development Kit <https://www.broadcom.com/products/pcie-switches-retimers/software-dev-kits>`_
* Upon successful installation, one should be able to acquire images with the manufacturer-provided PVCamTest software.

.. note::

    A static version of the Photometrics API is provided with this software. It is
    located in ``src/navigate/model/devices/APIs/photometrics/PyVCAM-master``. To
    install this API, navigate to that directory in your **navigate** environment and
    run :command:`python setup.py install`.

.. note::

    The most up-to-date version of PVCAM can be found on `GitHub <https://github.com/Photometrics/PyVCAM>`_.



