.. _plugin:

Plugin
======
Navigate is designed with extensibility. Users can seamlessly integrate custom
GUI plugins, device plugins, new feature plugins, and even define specific acquisition
modes.

Introduction
-------------------------------------

The Navigate **plugin system** gives user the flexibility to extend its functionaity according
to users' specific needs. Navigate will load plugins automatically and users can use their
plugins with Navigate seamlessly.

Plugin Tempate
-------------------------------------

A comprehensive **plugin template** is povided. Users could download the **plugin template** from
`github <https://github.com/TheDeanLab/navigate-plugin-template>`_ and build plugins on it.

Plugin Structure:

.. code-block:: none

    plugin_name/
        ├── controler/
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
        ├── plugin_acquisiton_mode.py
        └── plugin_config.yml 


.. note::

    The template shows a plugin with GUI, device, feature, feature_list and acquisition mode.
    If your plugin only incoporates some of these components, you should remove unused folders and files.


Plugin Configuration
--------------------

There should always have a **plugin_config.yml** file under the plugin folder, which tells Navigate
the plugin name, the GUI as a Tab or Popup and custom acquisition mode name. A typical plugin config
is:

.. code-block:: none

    name: Plugin Name
    view: Popup # or Tab
    acquisition_modes: 
      - name: Plugin Acquisition
        file_name: plugin_acquisition_mode.py


Plugin With GUI
---------------

Navigate supports a plugin with its own GUI. The custom plugin GUI can be integrated as a tab or a popup.
Users should specify the view option in `plugin_config.yml`. The name in the plugin_config.yml will be used
as a menu name if the plugin GUI as a popup. Users could find the menu under `Plugins` in Navigate window.


When creating a new plugin with GUI, ensure that the plugin name is consistent with the naming
conventions for the associated Python files (`plugin_name_controller.py` and `plugin_name_frame.py`).
Both Python filenames should be in lowercase.


For example, if your plugin is named `My Plugin` (there is a space in between), the associated Python files
should be named: "my_plugin_frame.py" and "my_plugin_controller.py"


Plugin With Device
------------------

The Navigate Software allows you to integrate a new device. There could be more than one device inside a plugin,
if they are different kinds of device, put them into different folders. For a kind of device, there should be
a `device_startup_functions.py` tells Navigate how to start the device and the reference name of the device in
system `configuration.yaml`.

Device type name and reference name are given as following:

.. code-block:: python

    DEVICE_TYPE_NAME = "plugin_device"  # Same as in configuraion.yaml, for example "stage", "filter_wheel", "remote_focus_device"...
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


The template of `device_startup_functions.py` could be find in the `template <https://github.com/TheDeanLab/navigate-plugin-template/blob/main/src/plugins-template/model/devices/plugin_device/device_startup_functions.py>`_.


Plugin With A New Feature
-------------------------
Navigate allows users to add new features. New feature objects and feature lists can be a plugin or a component
of a plugin. Features and feature lists are automatically loaded into Navigate.

Please visit `here <https://thedeanlab.github.io/navigate/feature_container/feature_container_home.html>`_ for details about how to build a new feature object and feature list.


Custom Acquisition Model
------------------------
Navigate offers seamless support for custom acquisition modes, and registering a new mode is straightforward.

1. Download the tempate `plugin_acquisition_mode.py <https://github.com/TheDeanLab/navigate-plugin-template/blob/main/src/plugins-template/plugin_acquisition_mode.py>`_ . 
2. Update the feature_list.

.. code-block:: python

    @AcquisitionMode
    class PluginAcquisitionMode:
        def __init__(self, name):
            self.acquisition_mode = name
            
            self.feature_list = [
                # update here
            ]

3. Update functions.

Users should tell Navigate what Navigate should do before and after acquisition.

.. code-block:: python

    def prepare_acquisition_controller(self, controller):
        # update here

    def end_acquisition_controller(self, controller):
        # update here
    
    def prepare_acquisition_model(self, model):
        # update here

    def end_acquisition_model(self, model):
        # update here

4. Register the acquisition mode in `plugin_config.yml`.

.. code-block:: none

    acquisition_modes: 
        - name: Custom Acquisition
            file_name: plugin_acquisition_mode.py



There are more plugin examples, please visit `Navigate <https://github.com/TheDeanLab/navigate/tree/develop/src/navigate/plugins>`_ and `Navigate Plugins <https://github.com/TheDeanLab/navigate-plugins>`_.
