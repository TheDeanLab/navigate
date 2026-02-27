.. _add_new_hardware_device:

=====================================
Add a New Hardware Device (Advanced)
=====================================

**navigate** supports several standard device categories:

- Cameras
- Data acquisition cards
- Deformable mirrors
- Filter wheels
- Galvo scanners
- Lasers
- Remote-focusing systems
- Shutters
- Stages
- Zoom devices

This guide explains how to add a new device (for example, ``CustomStage``) to one of these categories.

.. note::

   Integrating new hardware requires solid Python and object-oriented programming experience.

What Is the Device Abstraction Layer?
-------------------------------------

The device abstraction layer provides a shared control interface across vendors. For example, stage classes expose a common ``stop()`` method. When a user clicks :guilabel:`Stop Stage`, that command flows from controller to model to the concrete stage class (for example, ``CustomStage``), where it is translated into device-specific communication.

Device Integration Approaches
-----------------------------

There are two primary integration paths:

- **Plugin**: Recommended if you want to track upstream updates while maintaining custom hardware support. Plugins can also introduce non-standard device types. See :ref:`Plugin Architecture <plugin>` and :ref:`Write a Custom Device Plugin <advanced>`.
- **Fork**: Useful for internal development where deep core changes are required. In some cases, these changes can later be proposed upstream.

Device Class Creation
---------------------

- Create a device class in the appropriate directory under :file:`src/navigate/model/devices/`.
- Inherit from the correct abstract base class (for example, ``StageBase`` for a stage).
- Use CamelCase class names that describe the device (for example, ``NewportStage``).
- Place manufacturer-specific API wrappers in the relevant manufacturer/API directory.

Establish Device Communication
------------------------------

- Implement a dedicated connection function (for example, ``build_custom_stage_connection()``).
- Keep connection setup separate from the device class when possible.
- This separation allows direct hardware tests outside the full **navigate** runtime (for example, in a notebook or standalone script).

Device Class Constructor
------------------------

- Define ``__init__`` with the required startup parameters (typically ``microscope_name``, ``device_connection``, ``configuration``, and optional device identifiers).
- Load and validate settings from the configuration.
- Reuse the established connection object instead of creating a second connection inside the class.

For stages, this often includes mapping **navigate** axes to device axes (for example, ``{"x": "X", "y": "Y", "z": "Z"}``).

Device Class Methods
--------------------

- Implement required methods from the base class.
- Override defaults where needed for vendor behavior.
- Add device-specific methods only when they do not break shared interface expectations.

Startup and Configuration
-------------------------

- Register startup logic in :file:`src/navigate/model/device_startup_functions`.
- Parse configuration values and construct the connection/device objects there.
- Use retry logic (for example, ``auto_redial``) to handle transient communication failures.

Integration with Microscope Configurations
------------------------------------------

- Add the new device under the correct microscope entries in :file:`configuration.yaml`.
- Ensure startup wiring injects the new device connection into each configured microscope object that needs it.

Testing and Validation
----------------------

- Test the integration across the supported acquisition modes and expected error paths.
- Name test files as ``test_<module_name>.py``.
- Place device tests under :file:`test/model/devices/`.
- Use ``pytest`` for hardware and synthetic-path validation.

Following this workflow keeps new integrations consistent with the existing architecture and reduces long-term maintenance risk.
