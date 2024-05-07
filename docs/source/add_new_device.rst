======================================
 Add a New Hardware Device (Advanced)
======================================

**navigate** includes several standard hardware device types. These include:

- Cameras
- Data Acquisition Cards
- Filter Wheels
- Galvo Scanners
- Lasers
- Deformable Mirrors
- Remote Focusing Systems
- Shutters
- Stages
- Zoom Devices

To add a new piece of hardware to one of these device types requires knowledge about
the software's device abstraction layer. Here’s a detailed guide to help you
integrate new ``CustomStage`` device into **navigate**. The same principles work for
other device types.

.. note::
    A strong knowledge of Python and object-oriented programming is required to
    integrate new hardware devices into **navigate**.

----------------

What is the Device Abstraction Layer?
-------------------------------------

To ensure compatibility and extendability, **navigate** utilizes a device abstraction
layer, which allows the same commands to be used across different hardware devices.
For example, all stages in **navigate** are programmed to include the `stop()`
command, which can be used to stop the stage's movement. When someone
hits the :guilabel:`Stop Stage` button on the GUI, this action is relayed from the
``Controller`` to the ``Model`` and ultimately the ``CustomStage``, which communicates
with the hardware in a device-specific format to stop the stage's movement.

--------------

Device Integration Approaches
-----------------------------

There are two primary approaches to integrating new hardware into **navigate**:

- **Plugin**:
    If you want to continue to work with an up-to-date version of **navigate**, consider
    integrating your new hardware device as a plugin. This allows you to pull
    updates from the main repository without losing your custom hardware integration.
    It also allows you to integrate non-standard device types.
    Learn more about the plugin architecture :doc:`here <plugin/plugin_home>`, and
    how to write a custom plugin :doc:`here <advanced>`.
- **Fork**:
    Alternatively, you can fork the **navigate** repository on GitHub and modify it
    directly. This is useful for custom, in-house developments. In select
    circumstances, you can contribute your changes back to the main repository
    through a pull request. Please contact the **navigate** development team for
    guidance on this approach.

--------------

Device Class Creation
---------------------
-   New hardware devices must have a corresponding device class in navigate. To ensure
    consistency and reduce redundancy, each device must inherit the appropriate abstract
    base class. For instance, a ``CustomStage`` device would inherit from ``StageBase``.
-   Classes should follow CamelCase naming conventions and reflect the device they
    control (e.g., ``NewportStage`` for a stage from the manufacturer Newport).
-   Place the new device class within the appropriate device directory,
    `src/navigate/model/devices/`.
-   Place related API or hardware documentation within the appropriate manufacturer
    directory, typically under `src/navigate/model/devices/APIs/`.

--------------

Establish Device Communication
------------------------------

-   Each device requires a unique method to initialize a connection, which may
    involve APIs, serial communication, or other protocols. This method should be
    separate from the device class and is typically located at the beginning of the
    device file.
-   For example, a function named `build_custom_stage_connection()` would handle
    the connection setup for ``CustomStage`` class.
-   By separating the connection setup from the device class, you can easily
    interact with the hardware device outside of the larger **navigate** ecosystem,
    which can be useful for debugging and testing (e.g., within a Jupyter notebook).

--------------

Device Class Constructor
------------------------

-   The constructor for the device class (`__init__`) should accept parameters for
    the `microscope_name`, `device_connection`, `configuration_file`, and an optional
    `device_ID` (useful when multiple instances of the same device are used).
-   The constructor should load and enforce device settings from the
    `configuration_file`. For a new stage, this could be defining the axes mapping
    between **navigate** and the device, `{x:'X', y:'Y', z:'Z'}`.
-   Ensure the device class uses the connection established by your
    `build_custom_stage_connection` method.

--------------

Device Class Methods
--------------------

-   Implement any necessary device-specific methods within your device class.
-   Essential methods are inherited from the base class (e.g., ``StageBase`` for the
    ``CustomStage``), but you can override them or add new methods as needed for
    specialized functionality.

--------------

Startup and Configuration
-------------------------

-   Utilize or modify methods within `src/navigate/model/device_startup_functions` to
    configure and start your device upon system initialization.
-   These functions should handle configuration parsing and the device communication
    setup.
-   Implement a retry mechanism, such as `auto_redial`, to handle communication
    issues robustly, attempting multiple times before failing.

--------------

Integration with Microscope Object Configurations
------------------------------------------------

-   Each microscope configuration in **navigate** that uses the new device should
    receive a reference to the established communication object.
-   This setup is defined in the *configuration.yaml* and handled within the
    `device_startup_functions`, ensuring each configuration has access to the
    necessary hardware.

--------------

Testing and Validation
----------------------
-   Thoroughly test the new hardware integration to ensure it functions correctly
    within navigate, across all intended use cases and configurations.
-   The naming convention for test files is: `test_` + module name.
-   Device test files are located in `test\model\devices\`
-   Device testing utilizes the `pytest` package.

By following these steps, you can effectively integrate new hardware into the
**navigate** platform, enhancing its functionality and ensuring it meets specific
experimental needs.
