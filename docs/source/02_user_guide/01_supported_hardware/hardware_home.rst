====================
Supported Hardware
====================

.. _hardware_overview:

**navigate** provides access to a growing list of hardware devices. Information on how to configure each of these devices, including supported firmware, is provided here.

The operational backbone of navigate is the data acquisition device, which synchronizes all hardware devices. 
Navigate supports both National Instruments and Applied Scientific Instrumentation devices to perform this logic. 
Each is accompanied with advantages and disadvantages. A discussion can be found :ref:`here <daq-ni-vs-asi>` on these devices.

Additional devices are available by installing the **navigate-mmcore-plugin**. To learn more, please visit the **navigate-mmcore-plugin**
`documentation <https://thedeanlab.github.io/navigate-mmcore-plugin/>`_.

.. toctree::
   :caption: Devices
   :maxdepth: 4

   daq.rst
   camera.rst
   remote_focus.rst
   stage.rst
   filter_wheel.rst
   dichroic.rst
   galvo.rst
   laser.rst
   shutter.rst
   zoom.rst
   deformable_mirror.rst
