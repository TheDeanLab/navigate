====================
Supported Hardware
====================

.. _hardware_overview:

**navigate** supports a growing set of hardware devices. This section explains how to
configure each device class and highlights tested firmware/driver versions where
available.

The operational backbone of **navigate** is the data acquisition device, which
synchronizes all hardware devices. **navigate** supports both National Instruments and
Applied Scientific Instrumentation hardware for this role. A comparison is provided in
:ref:`daq-ni-vs-asi`.

Additional devices are available through **navigate-mmcore-plugin**. See the
`navigate-mmcore-plugin documentation <https://thedeanlab.github.io/navigate-mmcore-plugin/>`_.

.. admonition:: Before You Configure Hardware

   - **Operating system:** hardware control is primarily operated on Windows, but has
     also been used on Linux in some environments.
   - Complete :ref:`software_installation` and :ref:`configuring_navigate` first.
   - If hardware is not connected yet, you can still validate workflows using Virtual
     Devices with :command:`navigate -sh` (see :ref:`launching_navigate`).
   - Start with :doc:`daq` and :doc:`camera`, then configure motion/optics devices such
     as :doc:`stage`, :doc:`remote_focus`, and :doc:`zoom`.

.. toctree::
   :caption: Devices
   :maxdepth: 2

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
