.. _plugin:

===================
Plugin Architecture
===================

**navigate** is designed for extensibility. You can use plugins to add GUI elements, hardware devices, feature objects, feature lists, and custom acquisition modes.

Introduction to Plugins
=======================

The plugin system allows users to extend **navigate** without modifying the core codebase. Installed plugins are discovered automatically at startup.

Installing a Plugin
===================

After you build or download a plugin, you can install it from the GUI. In this example, we use the `navigate-confocal-projection plugin <https://github.com/TheDeanLab/navigate-confocal-projection>`_.

#. Open :menuselection:`Plugins --> Install Plugin`.

   .. image:: images/plugin_1.png
      :width: 60%
      :align: center
      :alt: Plugins menu showing Install Plugin option

#. Select the plugin folder (for example, ``ConfocalProjectionPlugin``) and click :guilabel:`Select`.

   .. image:: images/plugin_2.png
      :width: 60%
      :align: center
      :alt: Folder selection dialog for plugin installation

#. Confirm the success message.

   .. image:: images/plugin_3.png
      :width: 60%
      :align: center
      :alt: Confirmation message after plugin installation

#. Restart **navigate** to load the plugin.

Uninstalling a Plugin
=====================

#. Open :menuselection:`Plugins --> Uninstall Plugins`.

   .. image:: images/plugin_4.png
      :width: 60%
      :align: center
      :alt: Plugins menu showing Uninstall Plugins option

#. Select the plugin to remove.

   .. image:: images/plugin_5.png
      :width: 60%
      :align: center
      :alt: Plugin selection window for uninstall

#. Click :guilabel:`Uninstall`.

   .. image:: images/plugin_6.png
      :width: 60%
      :align: center
      :alt: Confirmation flow for plugin uninstall

#. Restart **navigate** to complete removal.

Designing a Plugin
==================

Using the Plugin Template
-------------------------

Use the official `navigate-plugin-template <https://github.com/TheDeanLab/navigate-plugin-template>`_ as a starting point.

Plugin structure:

.. code-block:: none

    plugin_name/
        ├── controller/
        │   ├── plugin_name_controller.py
        │   ├── ...
        ├── model/
        │   ├── devices/
        │   │   └── plugin_device/
        │   │       ├── device_startup_functions.py
        │   │       ├── plugin_device.py
        │   │       └── synthetic_plugin_device.py
        │   └── features/
        │       ├── plugin_feature.py
        │       ├── ...
        ├── view/
        │   ├── plugin_name_frame.py
        │   ├── ...
        ├── feature_list.py
        ├── plugin_acquisition_mode.py
        └── plugin_config.yml

.. note::

   The template includes optional components (GUI, devices, features, feature lists, and acquisition modes). Remove any folders or files you do not use.

Plugin Configuration
--------------------

Each plugin should include a ``plugin_config.yml`` file in the plugin root. It defines plugin metadata, view type, and optional acquisition modes.

Example:

.. code-block:: none

    name: Plugin Name
    view: Popup # or Tab
    acquisition_modes:
      - name: Plugin Acquisition
        file_name: plugin_acquisition_mode.py

Plugin GUI Elements
-------------------

Plugins can contribute GUI elements as either tabs or popups. Set the desired view in ``plugin_config.yml``.

- If ``view: Popup`` is used, the plugin appears under the :guilabel:`Plugins` menu.
- If ``view: Tab`` is used, the plugin appears beside the :ref:`Settings Notebooks <ui_settings_notebooks>`.

Use consistent lowercase filenames for GUI/controller modules. For example, if the plugin name is ``My Plugin``, use ``my_plugin_frame.py`` and ``my_plugin_controller.py``.

Plugin Devices
--------------

Plugins can define one or more hardware device types. For each device type, create a dedicated folder and provide ``device_startup_functions.py`` to define connection and startup behavior.

Device type names and reference keys are declared as:

.. code-block:: python

    DEVICE_TYPE_NAME = "plugin_device"  # For example: "stage", "filter_wheel"
    DEVICE_REF_LIST = ["type", "serial_number"]

Implement a connection loader:

.. code-block:: python

    def load_device(hardware_configuration, is_synthetic=False):
        # ...
        return device_connection

Implement device startup:

.. code-block:: python

    def start_device(microscope_name, device_connection, configuration, is_synthetic=False):
        # ...
        return device_object

See the template implementation in `device_startup_functions.py <https://github.com/TheDeanLab/navigate-plugin-template/blob/main/plugins_template/model/devices/plugin_device/device_startup_functions.py>`_.

Plugin Features
---------------

Plugins can contribute new feature objects and feature lists. These are discovered and loaded automatically at startup.

For implementation details, see :ref:`Feature Container <features>`.

Custom Acquisition Modes
------------------------

Plugins can register custom acquisition modes.

1. Start from the template `plugin_acquisition_mode.py <https://github.com/TheDeanLab/navigate-plugin-template/blob/main/plugins_template/plugin_acquisition_mode.py>`_.
2. Update ``feature_list``.

.. code-block:: python

    @AcquisitionMode
    class PluginAcquisitionMode:
        def __init__(self, name):
            self.acquisition_mode = name

            self.feature_list = [
                # update here
            ]

3. Implement controller/model lifecycle hooks as needed:

.. code-block:: python

    def prepare_acquisition_controller(self, controller):
        # update here

    def end_acquisition_controller(self, controller):
        # update here

    def prepare_acquisition_model(self, model):
        # update here

    def end_acquisition_model(self, model):
        # update here

4. Register the mode in ``plugin_config.yml``:

.. code-block:: none

    acquisition_modes:
        - name: Custom Acquisition
          file_name: plugin_acquisition_mode.py

For additional real-world examples, see the plugin repositories linked in the main documentation navigation.
