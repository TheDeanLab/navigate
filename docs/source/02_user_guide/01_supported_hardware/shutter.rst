========
Shutters
========

When only controlled with analog modulation, many laser sources do not
reduce their emitted intensity to 0 watts. In such cases, residual illumination subjects
the specimen to unnecessary irradiation between image acquisitions. Shutters overcome
this by completely blocking the laser, albeit on a much slower timescale than direct
modulation of the laser. With **navigate**, shutters automatically open at the start
of acquisition and close upon finish.

Most shutters are controlled via a digital voltage. When the voltage is high (e.g., >
2.5 V), the shutter is open, and when the voltage is low (e.g., < 2.5 V), the shutter
is closed.

------------

National Instruments (NI)
----------------------------

We can control these shutters using a digital output from a National
Instruments (NI) data acquisition card.

.. Note::

    If the shutter opens and closes immediately upon starting an acquisition, try a
    different port for the digital I/O on the NI data acquisition card. Some NI devices
    (e.g.PCIe-6738) have port/sample size limitations. If the port/sample size is
    exceeded, the shutter will not open. For example, on our `NI PCIe-6738 <https://www
    .ni.com/docs/en-US/bundle/pcie-6738-specs/page/specs.html>`_ using port 0 for the
    shutter causes this issue, but switching the shutter to any port 1 channel fixed it.
    In comparison, for the `NI PCIe-6259 <https://www.ni
    .com/docs/en-US/bundle/pci-pcie-pxi-pxie-usb-6259-specs/page/specs.html>`_,
    using port 0 had no averse effects.

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
