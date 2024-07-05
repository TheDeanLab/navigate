========
Shutters
========

When controlled with analog, digital, or mixed modulation, not all laser sources
reduce their emitted intensity to 0. In such cases, residual illumination subjects
the specimen to unnecessary irradiation between image acquisitions. Shutters overcome
this by completely blocking the laser, albeit on a much slower timescale than direct
modulation of the laser. With **navigate**, shutters automatically open at the start
of acquisition and close upon finish.

------------

Analog/Digital-Controlled Shutters
----------------------------------

Thorlabs shutters are controlled via a digital on off voltage.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            shutter:
              hardware:
                type: NI
                channel: PXI6249/port0/line0
                min: 0.0
                max: 5.0

|

------------------

Synthetic Shutter
-----------------
If no shutter is present, one must configure the software to use a synthetic
shutter.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            shutter:
              hardware:
                type: synthetic
                channel: PXI6249/port0/line0
                min: 0.0
                max: 5.0

|

------------------

Potential Issues and Solutions
-----------------

**Issue:**

Shutter opens and closes immediately upon starting any acquisition mode, no traceback error occuring.
Model Debug log files indicate that the shutter is correctly recognizing when it should be open/closed.

.. image:: docs/source/user_guide/hardware/images/Shutter_ModelDebug.png
    :align: center
    :alt: Examples of debug messages indicating opening/closing of the shutter

**Potential Solution:**

Try a different port for the digital I/O on the controller, making sure to update the port in your configuration file as well.
Some NI devices (e.g.PCIe-6738) have port/sample size limitations. If the port/sample size is exceeded, the shutter will not open.
For example, on our `NI PCIe-6738 <https://www.ni.com/docs/en-US/bundle/pcie-6738-specs/page/specs.html>`_
using port 0 for the shutter causes this issue, but switching the shutter to any port 1 channel fixed it.
In comparison, for the `NI PCIe-6259 <https://www.ni.com/docs/en-US/bundle/pci-pcie-pxi-pxie-usb-6259-specs/page/specs.html>`_,
using port 0 had no averse effects.


