.. _advanced:

=======================================
Write a Custom Device Plugin (Advanced)
=======================================

**navigate**'s :ref:`plugin system <plugin>` enables users to add new devices, features, and acquisition modes. In this guide, we add a new device type called ``CustomDevice`` and a dedicated GUI window to control it. This hypothetical device can move a set distance, rotate by a specified angle, and stop on command.

**navigate** plugins follow a Model-View-Controller architecture. The model contains device-specific code, the view contains GUI code, and the controller coordinates communication between them.

Initial Steps
-------------

Use the template plugin as your starting point.

* Go to `navigate-plugin-template <https://github.com/TheDeanLab/navigate-plugin-template>`_.
* In the upper right, click ``Use this template``, then ``Create a new repository``.
* In this repository, rename the ``plugin_device`` folder to ``custom_device``.
* Rename the file ``plugin_device.py`` to ``custom_device.py``.

Model Code
----------

Create a new custom device using the following code.

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

        def rotate(self, angle=0.1):
            """ Rotate the Custom Device

            Parameters
            ----------
            angle : float
                The angle of the rotation. Default is 0.1 degree.
            """
            print("*** Custom Device is rotating by", angle)

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

All devices should include synthetic versions, which allow the software to run without physical hardware connected. Following the same pattern as ``CustomDevice``, implement ``synthetic_device.py`` without hardware I/O calls.

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
            print("*** Synthetic Device received command: move", step_size)

        def stop(self):
            """ Stop the Synthetic Device """
            print("*** Synthetic Device received command: stop")

        def rotate(self, angle=0.1):
            """ Turn the Synthetic Device

            Parameters
            ----------
            angle : float
                The angle of the rotation. Default is 0.1 degree.
            """
            print("*** Synthetic Device received command: rotate", angle)

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

Edit ``device_startup_functions.py`` to tell **navigate** how to connect to and start ``CustomDevice``. This is where hardware connections are created. ``load_device()`` should return a connection object.

**navigate** initializes each device connection independently and passes that connection to the class that controls it (in this example, ``CustomDevice``). This allows startup with multiple microscope :ref:`configurations <multiple_microscopes>`, including configurations that share devices.

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
            return synthetic_device.SyntheticCustomDevice(
                microscope_name, device_connection, configuration
            )
        else:
            device_not_found(microscope_name, device_type)

View Code
---------
To add a GUI control window, go to the ``view`` folder, rename ``plugin_name_frame.py`` to ``custom_device_frame.py``, and edit the code as follows.

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

    **navigate** provides validated widgets that reduce user-input errors and runtime failures. Recommended options include:

    * ``LabelInput``, which combines a label and an input widget (used above for ``step_size`` and ``angle``).
    * Standard Tk widgets such as ``ttk.Entry`` via ``input_class``.
    * Additional validated widgets such as ``ValidatedSpinbox``, ``ValidatedEntry``, ``ValidatedCombobox``, and ``ValidatedMixin``.

    See :any:`navigate.view.custom_widgets` for details.

Controller Code
---------------
Next, build the controller. Open the ``controller`` folder, rename ``plugin_name_controller.py`` to ``custom_device_controller.py``, and edit the code as follows.

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

In this example, the ``custom_device`` sub-controller maps button clicks to ``move_device``, ``rotate_device``, and ``stop_device``. This triggers the following sequence:

    * The sub-controller passes the command to the parent controller, which is the main controller for the software.
    * The parent controller passes the command to the model, which runs in its own subprocess, using an event queue. This avoids tight coupling and reduces race conditions.
    * The model executes the command, and model-to-controller updates are relayed through another event queue.

Plugin Configuration
--------------------
Next, update the ``plugin_config.yml`` file as follows:

.. code-block:: yaml

    name: Custom Device
    view: Popup

Remove the folder ``./model/features``, the file ``feature_list.py``, and the file ``plugin_acquisition_mode.py``. The plugin folder structure is as follows.

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

Install the plugin using one of two methods:
    * Install by placing the entire plugin folder directly in ``navigate/plugins/``. In this example, place the ``custom_device`` folder and all contents under ``navigate/plugins/``.
    * Alternatively, install this plugin through the menu :menuselection:`Plugins --> Install Plugin` by selecting the plugin folder.

The plugin is now ready to use. You can reference ``CustomDevice`` in ``configuration.yaml`` as follows.

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

The ``custom_device`` will be loaded when **navigate** is launched, and it can be controlled through the GUI.
