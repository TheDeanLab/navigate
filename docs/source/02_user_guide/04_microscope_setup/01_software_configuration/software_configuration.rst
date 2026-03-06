.. _configuration_file:

======================
Advanced Configuration
======================

This page is the detailed reference for ``configuration.yaml`` and related
configuration files.

Before You Continue
-------------------

If you are still building your first working configuration, follow
:ref:`Configuring Navigate <configuring_navigate>` first. That page is optimized
for first-time setup.

Use this page when you need to:

* define multiple microscopes and inheritance,
* map hardware stage axes to logical axes,
* configure stage limits, offsets, and flip flags,
* tune zoom and waveform-related configuration files.

Configuration Files At A Glance
-------------------------------

* ``configuration.yaml``: hardware definitions, microscope definitions, limits,
  mappings, and core behavior.
* ``gui_configuration.yml``: GUI widget behavior defaults (for example, control
  step sizes and related widget behavior).
* ``multi_positions.yml``: saved multi-position table contents used by
  multi-position workflows.
* ``experiment.yml``: current runtime state (auto-generated if missing and
  auto-updated by **navigate**).
* ``waveform_constants.yml``: saved waveform parameter values.
* ``waveform_templates.yml``: default waveform-repeat behavior.
* ``rest_api_config.yml``: REST API endpoint configuration for API-dependent
  plugins.

By default, **navigate** uses a local configuration directory:

* Windows: ``C:\Users\Username\AppData\Local\.navigate\config``
* macOS/Linux: ``~/.navigate/config``

.. tip::

   To open this directory from the GUI, use
   :menuselection:`File --> Open Configuration Files`.

Safe Editing Notes
------------------

The highest-impact fields for behavior and hardware safety are:

* ``axes_mapping``
* ``flip_<axis>`` entries
* stage limits (``*_min`` / ``*_max``)
* stage offsets (``*_offset``)

After editing these fields, validate motion carefully before acquisition.

For practical configuration examples, see
:ref:`Setting up an Axially Swept Light-Sheet Microscope <setup_aslm>` and
:ref:`Implementations <implemented_microscopes>`.

.. _multiple_microscopes:

Microscope Configurations
-------------------------

The ``configuration.yaml`` file contains one or more microscope definitions.
Each microscope is represented as a YAML dictionary.

Switching between microscopes in **navigate** allows you to move between
configurations or imaging modes that may use shared or unique hardware.

.. code-block:: yaml

   microscopes:
       microscope1:
           ...
       microscope2:
           ...

Here, ``microscope1`` and ``microscope2`` are microscope names that use
different hardware combinations. Microscope names should not contain spaces or
special characters such as ``<``, ``\``, ``#``, ``%``, or ``?``.

Microscope Inheritance
----------------------

When multiple microscopes share most hardware, the configuration file can
become repetitive. **navigate** supports inheritance to reduce duplication.
In the following example, ``microscope2`` inherits from ``microscope1`` and
overrides only the camera configuration.

.. code-block:: yaml

   microscopes:
       microscope1:
           camera:
               hardware:
                   type: HamamatsuOrca
                   ...
           ...
       microscope2(microscope1):
           camera:
               hardware:
                   type: HamamatsuFusion
                   ...
           ...

Microscope Hardware Specification
---------------------------------

Each microscope definition is expected to include ``daq``, ``camera``,
``remote_focus_device``, ``galvo``, ``filter_wheel``, ``stage``, ``zoom``,
``shutter``, ``mirror``, and ``lasers`` sections. Unused devices can be set to
synthetic implementations.

Most setup details are documented in :ref:`Supported Hardware <hardware_overview>`.
Additional explanations for commonly edited microscope sections are provided
below.

.. _configure_stages:

Stage Subsection
^^^^^^^^^^^^^^^^

The ``stage`` section of each microscope definition does three things:

1. Maps stage hardware from the ``hardware`` section into the microscope.
2. Defines software movement limits for each axis.
3. Optionally defines joystick-controlled axes.

.. code-block:: yaml

   microscopes:
       microscope1:
           stage:
               hardware:
                 -
                   name: stage
                   type: ASI
                   serial_number: 123456789
                   axes: [x, y, z, f] # Software axes
                   axes_mapping: [M, Y, X, Z] # Hardware API axis mapping

                 -
                   name: stage
                   type: SyntheticStage
                   serial_number: 987654321
                   axes: [theta]

           joystick_axes: [x, y, z]
           x_max: 100000
           x_min: -100000
           y_max: 100000
           y_min: -100000
           z_max: 100000
           z_min: -100000
           f_max: 100000
           f_min: -100000
           theta_max: 360
           theta_min: 0

           x_offset: 0
           y_offset: 0
           z_offset: 0
           theta_offset: 0
           f_offset: 0

           flip_x: False
           flip_y: False
           flip_z: False
           flip_f: False

First, define software axes for each stage device and map API axis names to
software axis names with ``axes_mapping``. In the example above, ASI ``M`` is
mapped to software ``X``.

For ``stages``, **navigate** expects the logical axes ``X``, ``Y``, ``Z``,
``F``, and ``Theta`` to be available for each microscope. If a physical axis is
not present, define it as a ``SyntheticStage`` (as shown for ``Theta``).

The ``joystick_axes`` entry defines which logical axes may be controlled by a
joystick.

Axis bounds (``*_min`` and ``*_max``) define safe software movement limits to
help prevent collisions.

Axis offsets (``*_offset``) are used to register microscopes relative to each
other. If ``microscope1`` is the reference microscope, an inherited microscope
can use offsets to move to the same sample location.

Finally, set flip flags (``flip_x``, ``flip_y``, ``flip_z``, ``flip_f``) to
match expected directionality. Correct flip configuration is required for
reliable :ref:`multi-position <ui_multiposition>` behavior.

.. _software_configuration_additional_axes:

Additional Non-Canonical Stage Axes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to canonical logical axes ``X``, ``Y``, ``Z``, ``F``, and
``Theta``, you can define additional stage axes for specialized hardware.
Define these axes the same way as other stage entries, including appropriate
``*_min`` / ``*_max`` limits and ``*_offset`` values.

Additional axis identifiers must be unique within the microscope and must not
reuse canonical identifiers (``X``, ``Y``, ``Z``, ``F``, ``Theta``; similarly
``x``, ``y``, ``z``, ``f``, ``theta`` in YAML entries). Map custom hardware API
axes to these logical names through ``axes`` and ``axes_mapping``.

.. _software_configuration_stages:

Stage Axes Definition
^^^^^^^^^^^^^^^^^^^^^

Stage hardware coordinate systems often differ from optical coordinate
conventions. Use ``axes_mapping`` to map mechanical axes to **navigate** logical
axes.

By default, logical axes are interpreted as ``X``, ``Y``, ``Z``, ``Theta``
(rotation), and ``F`` (focus).

.. code-block:: yaml

   axes: [x, y, z, theta, f]
   axes_mapping: [x, y, z, r, f]

If a microscope's hardware ``Z`` axis corresponds to optical ``Y`` and hardware
``Y`` corresponds to optical ``Z``, map them as:

.. code-block:: yaml

   axes: [x, y, z, theta, f]
   axes_mapping: [x, z, y, r, f]

Joystick Axes Definition
^^^^^^^^^^^^^^^^^^^^^^^^

If you use a joystick, GUI controls can be disabled for joystick-controlled
axes. Define joystick axes in the stage section:

.. code-block:: yaml

   joystick_axes: [x, y, z]

.. note::

   Joystick axes should be defined in logical (optical) coordinates.
   For the axis-mapping example above, if joystick motion controls optical
   ``Y`` (hardware ``Z``), set:

.. code-block:: yaml

   joystick_axes: [y]

Zoom Subsection
^^^^^^^^^^^^^^^

The ``zoom`` section configures zoom devices (or other magnification-changing
hardware). For example, a Dynamixel actuator can control an Olympus MVXPLAPO
zoom wheel.

.. code-block:: yaml

   microscopes:
       microscope1:
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

Here, ``position`` defines actuator position values per zoom level.
``pixel_size`` defines effective pixel size at each zoom setting.
``stage_positions`` can compensate focus shifts between zoom values for specific
immersion media (for example, ``BABB``).

Even if your microscope has no zoom actuator, include a ``zoom`` section that
defines effective pixel size:

.. code-block:: yaml

   zoom:
     hardware:
       name: zoom
       type: SyntheticZoom
       servo_id: 1
     position:
       N/A: 0
     pixel_size:
       N/A: 0.168

.. _experiment_file:

Experiment File
---------------

The ``experiment.yml`` file stores the current software state, including laser
parameters, camera parameters, save options, and z-stack settings. Users
normally do not need to edit this file manually. **navigate** updates it
automatically during use and on exit. If this file is missing or malformed,
**navigate** regenerates a safe default based on ``configuration.yaml``.

.. _configure_waveforms_constants:

Waveform Constants File
-----------------------

The ``waveform_constants.yml`` file stores waveform parameters exposed through
:menuselection:`Microscope Configuration --> Waveform Parameters`.
Users normally do not need to edit this file manually. **navigate** updates it
automatically during use and on exit.

.. _configure_waveform_templates:

Waveform Templates File
-----------------------

The ``waveform_templates.yml`` file stores default repeat behavior for specific
waveforms. Edit this file only when adding new waveform behaviors.

REST API Configuration File
---------------------------

The ``rest_api_config.yml`` file defines REST API endpoints used for get/post
operations. This is only needed when using plugins that depend on the REST API,
such as ilastik integration. For setup details, see
:ref:`case_study_ilastik`.

Post-Edit Validation Checklist
------------------------------

After manual configuration edits:

1. Launch in synthetic mode first (``navigate -sh``) to confirm the file loads.
2. Launch with hardware and verify stage-direction behavior on each axis.
3. Confirm limits and offsets by testing short, safe moves near expected bounds.
4. Verify camera orientation and flip behavior against stage movement.
5. Confirm multi-position moves go in the expected direction before running long acquisitions.
