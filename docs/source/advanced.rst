==============================
Write a Custom Plugin (Expert)
==============================

navigate's :doc:`plugin system <plugin/plugin_home>` enables us to
easily incoporate new devices and integrate new features and acquisition modes. In this
guide, we will add a new device—let's call it 'custom_device' and a GUI window to control the 
newdevice. This custom device is capable of moving a certain distance, rotating a specified 
degree, and applying force to halt its movement.

First, fork `navigate-plugin-template <https://github.com/TheDeanLab/navigate-plugin-template>`_ .

Then, rename the 'plugin_device' folder to 'custom_device'. Rename the file 'plugin_device.py' to 'custom_device.py'.
Edit the code as follows: 

.. code-block:: python

    class CustomDevice:
        def __init__(self, device_connection, *args):
            self.device_connection = device_connection

        def move(self, step_size=1.0):
            print("*** Custom Device is moving by", step_size)

        def stop(self):
            print("*** Stopping the Custom Device!")

        def turn(self, angle=0.1):
            print("*** Custom Device is turning by", angle)

        @property
        def commands(self):
            return {
                "move_custom_device": lambda *args: self.move(args[0]),
                "stop_custom_device": lambda *args: self.stop(),
                "rotate_custom_device": lambda *args: self.rotate(args[0]),
            }


Edit the code in 'synthetic_device.py' as follows:

.. code-block:: python

    class SyntheticDevice:
    def __init__(self, device_connection, *args):
        pass

    def move(self, step_size=1.0):
        print("*** Systhetic Device receive command: move", step_size)

    def stop(self):
        print("*** Systhetic Device receive command: stop")

    def rotate(self, angle=0.1):
        print("*** Systhetic Device receive command: turn", angle)

    @property
    def commands(self):
        return {
            "move_custom_device": lambda *args: self.move(args[0]),
            "stop_custom_device": lambda *args: self.stop(),
            "rotate_custom_device": lambda *args: self.rotate(args[0]),
        }


Now, let's edit `device_startup_functions.py` which tells Navigate how to connect and start
the 'custom_device'.

.. code-block:: python

    import os
    from pathlib import Path

    from navigate.tools.common_functions import load_module_from_file

    from navigate.model.device_startup_functions import (
        auto_redial,
        device_not_found,
        DummyDeviceConnection,
    )

    DEVICE_TYPE_NAME = "custom_device"
    DEVICE_REF_LIST = ["type"]


    def load_device(configuration, is_synthetic=False):
        return DummyDeviceConnection()


    def start_device(microscope_name, device_connection, configuration, is_synthetic=False):
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


Now, let's add a GUI control window. Navigate to the 'view' folder, rename 
'plugin_name_frame.py' to 'custom_device_frame.py', and edit the code as follows:

.. code-block:: python

    import tkinter as tk
    from tkinter import ttk

    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput


    class CustomDeviceFrame(ttk.Frame):

        def __init__(self, root, *args, **kwargs):
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

Now, let's build a controller. Navigate to the 'controller' folder, rename 
'plugin_name_controller.py' to 'custom_device_controller.py', and edit the code
as follows:

.. code-block:: python

    import tkinter as tk

    from navigate.controller.sub_controllers.gui_controller import GUIController


    class CustomDeviceController(GUIController):
        def __init__(self, view, parent_controller=None):

            super().__init__(view, parent_controller)

            self.variables = self.view.get_variables()
            self.buttons = self.view.buttons

            self.buttons["move"].configure(command=self.move_device)
            self.buttons["rotate"].configure(command=self.rotate_device)
            self.buttons["stop"].configure(command=self.stop_device)

        def move_device(self, *args):
            self.parent_controller.execute(
                "move_custom_device", self.variables["step_size"].get()
            )

        def rotate_device(self, *args):
            self.parent_controller.execute(
                "rotate_custom_device", self.variables["angle"].get()
            )

        def stop_device(self, *args):
            self.parent_controller.execute("stop_custom_device")


Then, let's update the 'plugin_config.yml' file as follows:

.. code-block:: none

    name: Custom Device
    view: Popup


Now, let's remove the folder './model/features', the file 'feature_list.py', and
the file 'plugin_acquisition_mode.py'. The plugin folder structure is as follows:

.. code-block:: none

    custom_device/
        ├── controler/
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


Now, let's install this plugin. There are two ways to install a plugin. You could install
a plugin by putting the whole plugin folder directly into "navigate/plugins/". In this example,
put "custom_device" folder and all its contents into "navigate/plugins". Another way, you could
install this plugin through the menu :menuselection:`Plugins --> Install Plugin`, select the plugin
folder. Then the plugin is ready to use. For this plugin, you could specify a CustomDevice in the
`configuration.yaml` as follows:

.. code-block:: none

    microscopes:
        Mesoscale:
            daq:
                hardware:
                    name: daq
                    type: NI
            ...
            custom_device:
                hardware:
                    type: CustomDevice
            ...
            

This custom device will be loaded when you launch Navigate, and you could controller this device
through the GUI now.