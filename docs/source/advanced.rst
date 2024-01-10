==============================
Write a Custom Plugin (Expert)
==============================

**navigate**'s :doc:`plugin system <plugin/plugin_home>` enables users to
easily incorporate new devices and integrate new features and acquisition modes. In this
guide, we will add a new device, titled `custom_device`, and a dedicated GUI window to control it.
This hypothetical `custom_device` is capable of moving a certain distance,
rotating a specified number of degrees, and applying a force to halt its movement.

Like **navigate**, plugins are implemented using a Model-View-Controller architecture. The model
contains the device-specific code, the view contains the GUI code, and the
controller contains the code that communicates between the model and the view.

-----------------

Initial Steps
-------------

To ease the addition of a new plugin, we have created a template plugin that can be used as a starting point.

* Fork the `navigate-plugin-template <https://github.com/TheDeanLab/navigate-plugin-template>`_.
* Rename the `plugin_device` folder to `custom_device`.
* Rename the file `plugin_device.py` to `custom_device.py`.

-----------------

Model Code
----------

* Edit the code that communicates with the device as follows:

.. code-block:: python

    class CustomDevice:
        """ A Custom Device Class """
        def __init__(self, device_connection, *args):
            """ Initialize the Custom Device

            Parameters
            ----------
            device_connection : object
                The device connection object
            args : list
                The arguments for the device
            """
            self.device_connection = device_connection

        def move(self, step_size=1.0):
            """ Move the Custom Device

            Parameters
            ----------
            step_size : float
                The step size of the movement. Default is 1.0 micron.
            """
            print("*** Custom Device is moving by", step_size)

        def stop(self):
            """ Stop the Custom Device """
            print("*** Stopping the Custom Device!")

        def turn(self, angle=0.1):
            """ Turn the Custom Device

            Parameters
            ----------
            angle : float
                The angle of the rotation. Default is 0.1 degree.
            """
            print("*** Custom Device is turning by", angle)

        @property
        def commands(self):
            """ Return the commands for the Custom Device

            Returns
            -------
            dict
                The commands for the Custom Device
            """
            return {
                "move_custom_device": lambda *args: self.move(args[0]),
                "stop_custom_device": lambda *args: self.stop(),
                "rotate_custom_device": lambda *args: self.rotate(args[0]),
            }


* All devices are accompanied by synthetic versions, which enables the software to run without the
  hardware connected. Thus, in a manner that is similar to the `CustomDevice` class, we
  edit the code in `synthetic_device.py`, albeit without any calls to the device itself:

.. code-block:: python

    class SyntheticCustomDevice:
        """ A Synthetic Device Class """
        def __init__(self, device_connection, *args):
            """ Initialize the Synthetic Device

            Parameters
            ----------
            device_connection : object
                The device connection object
            args : list
                The arguments for the device
            """
            pass

        def move(self, step_size=1.0):
            """ Move the Synthetic Device

            Parameters
            ----------
            step_size : float
                The step size of the movement. Default is 1.0 micron.
            """
            print("*** Synthetic Device receive command: move", step_size)

        def stop(self):
            """ Stop the Synthetic Device """
            print("*** Synthetic Device receive command: stop")

        def rotate(self, angle=0.1):
            """ Turn the Synthetic Device

            Parameters
            ----------
            angle : float
                The angle of the rotation. Default is 0.1 degree.
            """
            print("*** Synthetic Device receive command: turn", angle)

        @property
        def commands(self):
            """ Return the commands for the Synthetic Device.

            Returns
            -------
            dict
                The commands for the Synthetic Device
             """
            return {
                "move_custom_device": lambda *args: self.move(args[0]),
                "stop_custom_device": lambda *args: self.stop(),
                "rotate_custom_device": lambda *args: self.rotate(args[0]),
            }


* Edit `device_startup_functions.py` which tells **navigate** how to connect and start the `custom_device`.

.. code-block:: python

    # Standard library imports
    import os
    from pathlib import Path

    # Third party imports

    # Local application imports
    from navigate.tools.common_functions import load_module_from_file
    from navigate.model.device_startup_functions import (
        auto_redial,
        device_not_found,
        DummyDeviceConnection,
    )

    DEVICE_TYPE_NAME = "custom_device"
    DEVICE_REF_LIST = ["type"]

    def load_device(configuration, is_synthetic=False):
        """ Load the Custom Device

        Parameters
        ----------
        configuration : dict
            The configuration for the Custom Device
        is_synthetic : bool
            Whether the device is synthetic or not. Default is False.

        Returns
        -------
        object
            The Custom Device object
        """
        return DummyDeviceConnection()

    def start_device(microscope_name, device_connection, configuration, is_synthetic=False):
        """ Start the Custom Device

        Parameters
        ----------
        microscope_name : str
            The name of the microscope
        device_connection : object
            The device connection object
        configuration : dict
            The configuration for the Custom Device
        is_synthetic : bool
            Whether the device is synthetic or not. Default is False.

        Returns
        -------
        object
            The Custom Device object
        """
        if is_synthetic:
            device_type = "synthetic"
        else:
            device_type = configuration["configuration"]["microscopes"][microscope_name][
                "custom_device"
            ]["hardware"]["type"]

        if device_type == "CustomDevice":
            custom_device = load_module_from_file(
                "custom_device",
                os.path.join(Path(__file__).resolve().parent, "custom_device.py"),
            )
            return custom_device.CustomDevice(
                microscope_name, device_connection, configuration
            )
        elif device_type == "synthetic":
            synthetic_device = load_module_from_file(
                "custom_synthetic_device",
                os.path.join(Path(__file__).resolve().parent, "synthetic_device.py"),
            )
            return synthetic_device.SyntheticDevice(
                microscope_name, device_connection, configuration
            )
        else:
            device_not_found(microscope_name, device_type)

.. tip::

    **navigate** establishes communication with each device independently, and
    passes the instance of that device to class that controls it (e.g., in this case, the
    `CustomDevice` class). This allows **navigate** to be initialized with multiple imaging configurations,
    some of which may share devices.

-----------------

View Code
---------
* To add a GUI control window, go to the `view` folder, rename `plugin_name_frame.py` to `custom_device_frame.py`, and edit the code as follows:

.. code-block:: python

    # Standard library imports
    import tkinter as tk
    from tkinter import ttk

    # Third party imports

    # Local application imports
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput


    class CustomDeviceFrame(ttk.Frame):
        """ The Custom Device Frame """
        def __init__(self, root, *args, **kwargs):
            """ Initialize the Custom Device Frame

            Parameters
            ----------
            root : object
                The root Tk object
            args : list
                The arguments for the Custom Device Frame
            kwargs : dict
                The keyword arguments for the Custom Device Frame
            """
            ttk.Frame.__init__(self, root, *args, **kwargs)

            # Formatting
            tk.Grid.columnconfigure(self, "all", weight=1)
            tk.Grid.rowconfigure(self, "all", weight=1)

            # Dictionary for widgets and buttons
            #: dict: Dictionary of the widgets in the frame
            self.inputs = {}

            self.inputs["step_size"] = LabelInput(
                parent=self,
                label="Step Size",
                label_args={"padding": (0, 0, 10, 0)},
                input_class=ttk.Entry,
                input_var=tk.DoubleVar(),
            )
            self.inputs["step_size"].grid(row=0, column=0, sticky="N", padx=6)
            self.inputs["step_size"].label.grid(sticky="N")
            self.inputs["angle"] = LabelInput(
                parent=self,
                label="Angle",
                label_args={"padding": (0, 5, 25, 0)},
                input_class=ttk.Entry,
                input_var=tk.DoubleVar(),
            )
            self.inputs["angle"].grid(row=1, column=0, sticky="N", padx=6)
            self.inputs["angle"].label.grid(sticky="N")

            self.buttons = {}
            self.buttons["move"] = ttk.Button(self, text="MOVE")
            self.buttons["rotate"] = ttk.Button(self, text="ROTATE")
            self.buttons["stop"] = ttk.Button(self, text="STOP")
            self.buttons["move"].grid(row=0, column=1, sticky="N", padx=6)
            self.buttons["rotate"].grid(row=1, column=1, sticky="N", padx=6)
            self.buttons["stop"].grid(row=2, column=1, sticky="N", padx=6)

        # Getters
        def get_variables(self):
            variables = {}
            for key, widget in self.inputs.items():
                variables[key] = widget.get_variable()
            return variables

        def get_widgets(self):
            return self.inputs

.. tip::

    **navigate** comes equipped with a large number of validated widgets,
    which prevent users from entering invalid values that can crash the program or result in
    undesirable outcomes. It is highly recommended that you use these, which include the following:

        * The `LabelInput` widget conveniently combines a label and an input widget into a single object.
          It is used to create the `step_size` and `angle` widgets in the code above.

        * The `LabelInput` widget can accept multiple types of `input_class` objects,
          which can include standard tkinter widgets (e.g., spinbox, entry, etc.) or custom
          widgets. In this example, we use the `ttk.Entry` widget.

        * Other examples of validated widgets include a `ValidatedSpinbox`, `ValidatedEntry`,
          `ValidatedCombobox`, and `ValidatedMixin`.

        * Please see the :any:`navigate.view.custom_widgets` module for more details.


-----------------

Controller Code
----------------
Now, let's build a controller. Open the 'controller' folder, rename
'plugin_name_controller.py' to 'custom_device_controller.py', and edit the code
as follows:

.. code-block:: python

    # Standard library imports
    import tkinter as tk

    # Third party imports

    # Local application imports
    from navigate.controller.sub_controllers.gui_controller import GUIController


    class CustomDeviceController(GUIController):
        """ The Custom Device Controller """
        def __init__(self, view, parent_controller=None):
            """ Initialize the Custom Device Controller

            Parameters
            ----------
            view : object
                The Custom Device View object
            parent_controller : object
                The parent (e.g., main) controller object
            """
            super().__init__(view, parent_controller)

            # Get the variables and buttons from the view
            self.variables = self.view.get_variables()
            self.buttons = self.view.buttons

            # Set the trace commands for the variables associated with the widgets in the View.
            self.buttons["move"].configure(command=self.move_device)
            self.buttons["rotate"].configure(command=self.rotate_device)
            self.buttons["stop"].configure(command=self.stop_device)

        def move_device(self, *args):
            """ Listen to the move button and move the Custom Device upon clicking.

            Parameters
            ----------
            args : list
                The arguments for the move_device function. Should be included as the tkinter event
                is passed to this function.
            """
            self.parent_controller.execute(
                "move_custom_device", self.variables["step_size"].get()
            )

        def rotate_device(self, *args):
            """ Listen to the rotate button and rotate the Custom Device upon clicking.

            Parameters
            ----------
            args : list
                The arguments for the rotate_device function. Should be included as the tkinter event
                is passed to this function.
            """
            self.parent_controller.execute(
                "rotate_custom_device", self.variables["angle"].get()
            )

        def stop_device(self, *args):
            """ Listen to the stop button and stop the Custom Device upon clicking.

            Parameters
            ----------
            args : list
                The arguments for the stop_device function. Should be included as the tkinter event
                is passed to this function.
            """
            self.parent_controller.execute("stop_custom_device")


* In each case above, the sub-controller for the `custom-device` establishes what actions should take
  place once a button in the view is clicked. In this case, the methods `move_device`, `rotate_device`, and
  `stop_device`.
* This triggers a sequence of events that include:
    * The sub-controller passes the command to the parent controller, which is the main controller
      for the software.
    * The parent controller passes the command to the model, which is operating in its own sub-process,
      using an event queue. This eliminates the need for the controller to know anything about the model
      and prevents race conditions.
    * The model then executes command, and any updates to the controller from the model are relayed
      using another event queue.

-----------------

Plugin Configuration
--------------------
* Next, update the 'plugin_config.yml' file as follows:

.. code-block:: yaml

    name: Custom Device
    view: Popup


* Remove the folder `./model/features`, the file `feature_list.py`, and
  the file `plugin_acquisition_mode.py`. The plugin folder structure is as follows:

.. code-block:: none

    custom_device/
        ├── controller/
        │   └── custom_device_controller.py
        |
        ├── model/
        |   └── devices/
        │       └── custom_device/
        │           ├── device_startup_functions.py
        │           ├── custom_device.py
        │           └── synthetic_device.py              
        ├── view/
        |   └── custom_device_frame.py
        │
        └── plugin_config.yml 


* Install the plugin using one of two methods:
    * You can install a plugin by putting the whole plugin folder directly into ``navigate/plugins/``.
      In this example, put "custom_device" folder and all its contents into "navigate/plugins".
    * You can install this plugin through the menu :menuselection:`Plugins --> Install Plugin` by selecting the plugin
      folder.
* The plugin is ready to use. For this plugin, you can now specify a CustomDevice in the
  `configuration.yaml` as follows:

.. code-block:: yaml

    microscopes:
        microscope_1:
            daq:
                hardware:
                    name: daq
                    type: NI
            ...
            custom_device:
                hardware:
                    type: CustomDevice
            ...
            

* The `custom_device` will be loaded when you launch **navigate**, and you can now control this device through the GUI now.