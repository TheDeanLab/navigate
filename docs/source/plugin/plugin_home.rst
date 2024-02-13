.. _plugin:

====================
Plugin Architecture
====================

**navigate** is designed with extensibility. Users can seamlessly integrate custom
GUI plugins, device plugins, new feature plugins, and even define specific acquisition
modes.

-------------------------------------

Introduction to Plugins
########################

The **navigate** **plugin system** gives users the flexibility to extend its functionality according
to their specific needs. **navigate** will load plugins automatically and users can use their
plugins with **navigate** seamlessly.

-----------

Installing a Plugin
####################

Once you've built a plugin or downloaded a **navigate** plugin, you can easily install it.
Here, we have downloaded the `Navigate Confocal-Projection Plugin <https://github.com/TheDeanLab/navigate-confocal-projection>`_.

#. You can install the **navigate-confocal-projection** plugin by selecting the menu
   :menuselection:`Plugins --> Install Plugin`.


   .. image:: images/plugin_1.png


#. Select the folder `ConfocalProjectionPlugin` and click :guilabel:`Select`.
   The plugin is now installed.


   .. image:: images/plugin_2.png

   .. image:: images/plugin_3.png


#. Restart **navigate** to use this installed plugin.


-----------

Uninstalling a Plugin
#####################

Uninstalling a plugin is very easy.

#. Select :menuselection:`Plugins --> Uninstall Plugins`. This will open a
   popup window where you can see all of the currently installed plugins.

   .. image:: images/plugin_4.png


#. Select the plugin you want to uninstall.

   .. image:: images/plugin_5.png


#. Click :guilabel:`Uninstall`.

   .. image:: images/plugin_6.png


#. Restart **navigate** to fully remove the uninstalled plugin.



-------------------------------------

Designing a Plugin
##########################

Using a Plugin Template
-------------------------------------

A comprehensive **plugin template** is provided. Users could download the **plugin template** from
`github <https://github.com/TheDeanLab/navigate-plugin-template>`_ and build plugins on it.

Plugin Structure:

.. code-block:: none

    plugin_name/
        ├── controller/
        │   ├── plugin_name_controller.py
        |   ├── ...
        ├── model/
        |   ├── devices/
        │   │   └── plugin_device/
        │   │       ├── device_startup_functions.py
        │   │       ├── plugin_device.py
        │   │       └── synthetic_plugin_device.py
        │   └── features/
        │           ├── plugin_feature.py
        │           ├── ...
        │               
        ├── view/
        |   ├── plugin_name_frame.py
        |   ├── ...
        │
        ├── feature_list.py
        ├── plugin_acquisition_mode.py
        └── plugin_config.yml 


.. note::

    The template shows a plugin with GUI, device, feature, feature_list and acquisition mode.
    If your plugin only incorporates some of these components, you should remove unused folders and files.

-------------------------------------

Plugin Configuration
--------------------

There should always have a ``plugin_config.yml`` file under the plugin folder, which tells **navigate**
the plugin name, the GUI as a Tab or Popup and custom acquisition mode name. A typical plugin config
is:

.. code-block:: none

    name: Plugin Name
    view: Popup # or Tab
    acquisition_modes: 
      - name: Plugin Acquisition
        file_name: plugin_acquisition_mode.py

-------------------------------------

Plugin GUI Elements
--------------------

**navigate** supports plugins with their own GUIs. A custom plugin GUI can be integrated as a tab or a popup.
Users should specify a view option in ``plugin_config.yml``. If it is a popup, users can find the plugin under 
the :guilabel:`Plugins` menu in the **navigate** window. If it is a tab, it will appear next to the 
:ref:`Settings Notebooks <user_guide/gui_walkthrough:settings notebooks>`.


When creating a new plugin with a GUI, ensure that the plugin name is consistent with the naming
conventions for the associated Python files (``plugin_name_controller.py`` and ``plugin_name_frame.py``).
Both Python filenames should be in lowercase.


For example, if your plugin is named "My Plugin" (there is a space in between), the associated Python files
should be named: ``my_plugin_frame.py`` and ``my_plugin_controller.py``.

-------------------------------------

Plugin Devices
------------------

The **navigate** plugin architecture allows you to integrate new hardware device. There can be more than one 
device inside a plugin. If they are different kinds of device, please put them into different folders. For each
kind of device, there should be a ``device_startup_functions.py`` telling **navigate** how to start the device
and indicating the reference name of the device to be used in ``configuration.yaml``.

Device type name and reference name are given as following:

.. code-block:: python

    DEVICE_TYPE_NAME = "plugin_device"  # Same as in configuration.yaml, for example "stage", "filter_wheel", "remote_focus_device"...
    DEVICE_REF_LIST = ["type", "serial_number"]


A function to load the device connection should be given,

.. code-block:: python

    def load_device(configuration, is_synthetic=False):
        # ...
        return device_connection


A function to start the device should be given,

.. code-block:: python

    def start_device(microscope_name, device_connection, configuration, is_synthetic=False):
        # ...
        return device_object


The template for ``device_startup_functions.py`` can be found in the `plugin template <https://github.com/TheDeanLab/navigate-plugin-template/blob/main/src/plugins-template/model/devices/plugin_device/device_startup_functions.py>`_.

-------------------------------------

Plugin Features
-------------------------
**navigate** allows users to add new features. New feature objects and feature lists can each be a plugin or components
of a plugin. Features and feature lists are automatically loaded into **navigate**.

Please visit `here <https://thedeanlab.github.io/**navigate**/feature_container/feature_container_home.html>`_ for details about how to build a new feature object and feature list.

-------------------------------------

Custom Acquisition Modes
------------------------
Navigate offers seamless support for custom acquisition modes, and registering a new mode is straightforward.

1. Download the template for `plugin_acquisition_mode.py
<https://github.com/TheDeanLab/navigate-plugin-template/blob/main/plugins-template/plugin_acquisition_mode.py>`_

2. Update the ``feature_list``.

.. code-block:: python

    @AcquisitionMode
    class PluginAcquisitionMode:
        def __init__(self, name):
            self.acquisition_mode = name
            
            self.feature_list = [
                # update here
            ]

3. Update the functions.

Users should tell **navigate** what to do before and after acquisition using the following functions.

.. code-block:: python

    def prepare_acquisition_controller(self, controller):
        # update here

    def end_acquisition_controller(self, controller):
        # update here
    
    def prepare_acquisition_model(self, model):
        # update here

    def end_acquisition_model(self, model):
        # update here

4. Register the acquisition mode in ``plugin_config.yml``.

.. code-block:: none

    acquisition_modes: 
        - name: Custom Acquisition
            file_name: plugin_acquisition_mode.py


-----------

For more plugin examples, please visit `navigate <https://github.com/TheDeanLab/navigate/tree/develop/src/navigate/plugins>`_ and `Navigate Plugins <https://github.com/TheDeanLab/navigate-plugins>`_.
