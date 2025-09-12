=======================
Software Architecture
=======================

.. image:: images/architecture.png
    :align: center
    :alt: Software Architecture

.. _software-architecture-section:

Model View Controller (MVC)
============================

The architecture of **navigate** is designed following the industry-standard Model-View-Controller (MVC) pattern. In this structure:

- **Model**: The model operates in its own subprocess and is responsible for communicating with hardware and performing image handling and processing tasks. Communication with the controller is managed through event queues, ensuring efficient data handling.
- **View**: The view is responsible for displaying the user interface and communicating with the controller. Each graphical user interface (GUI) window, such as the camera display and autofocusing module, is controlled by a dedicated sub-controller. These sub-controllers are responsible for relaying information back to the main controller, maintaining a clear separation of functionality.
- **Controller**: Acts as the central unit that manages the flow of data between the model and the view components, coordinating the application's overall functionality. It relays user input in the form of traces and commands to the model and relays model output in the form of images and data to the view.

ASIModel
========
The **ASIModel** is a specialized model designed to interface with ASI hardware. It extends the base model class and works as follows:

- **Full Control by Tiger Controller**: The Tiger Controller manages all timing and triggering for the hardware components, ensuring synchronized operation.
- **Hardware Control Loop**: A control loop is implemented by the `TGPLC <https://asiimaging.com/docs/tiger_programmable_logic_card>`_. 

Instead of providing numpy arrays representing waveforms, the ASIModel sends serial commands to the Tiger Controller to configure and execute common 
waveforms (sine, triangle, sawtooth, step) on specified channels. These waveforms are triggered by the TGPLC. This triggering is all set up in the 
Tiger Controller API file (``asi_tiger_controller.py``) in the function ``setup_control_loop()``:

.. code-block:: python

    def setup_control_loop(self):
        commands = [
            # Cell 2, a one-shot triggered by the rising edge of Cell 1
            "6 m e = 2",
            "6 cca y = 8 z = 10",
            "6 ccb x = 1 y = 192",
            # Cell 3, delay cell that is used to sync up the loop after Galvo initialization
            # Delay time is based on the start delay variable (in 1/4 ms)
            "6 m e = 3",
            f"6 cca y = 9 z = {start_delay}",
            "6 ccb x = 1 y = 192",
        ]

The commands above show how cells are configured. 

- 6 refers to the address of the TGPLC. 
- "m e" points to the cell to be configured. 
- "cca y" specifies the type of cell.
- "cca z" specifies its configuration. 
- The "ccb" commands refer to the inputs to the cell. 

This is better explained in a table in the `TGPLC documentation <https://asiimaging.com/docs/tiger_programmable_logic_card>`_.
To modify the control loop, one can modify the commands in this function accordingly. Functionality includes, but is not limited to:

- triggering analog and digital waveforms
- incorporating specific delays
- variable conditions for stopping the loop

.. code-block:: python

    def setup_control_loop(self):
        galvo_commands = [
            # Sets the output of Cell 2 as the input to the TTL corresponding to
            # the first Galvo
            f"6 m e = 42", # Address for TTL1,which corresponds to galvo axis A
            "6 cca y = 2 z = 2",
            # Sets the output of Cell 10 as the input to the TTL corresponding to
            # the second Galvo
            f"6 m e = 44", # Address for TTL3, which corresponds to galvo axis B
            "6 cca y = 2 z = 10",
        ]

The commands above show how to trigger analog waveforms. First, you point to the backplane 
address corresponding to the analog axis. We have determined the following connections from our experience:

==== ==== ====
Axes Addr TTL#
==== ==== ====
A, H  42  TTL1
B, I  44  TTL3
C, J  46  TTL5
D, K  48  TTL7
==== ==== ====

- "cca y = 2" in this case specifies Push-Pull output 
- "cca z" specifies the logic cell that is the input to this output.

The image below depicts one configuration of the control loop (corresponding specifically to navigate's continuous mode):

.. image:: images/control_loop.png
    :align: center
    :alt: Control Loop

Extendability
============================

To maximize the extendability of **navigate**, it incorporates:

- **REST-API Level**: A RESTful API layer is included to facilitate communication with external libraries, ensuring compatibility and extendability. Data is exchanged to the external environment through a http server, allowing for rapid and seamless integration with other systems. Data does not need to be saved locally to be loaded by the external system.
- **Plugin Layer**: Offers the flexibility to integrate non-supported devices through plugins, enhancing the system's adaptability to various hardware.

Data Acquisition and Processing
===============================

**navigate** employs a feature container for running acquisition routines, characterized by:

- **Reconfigurable Workflows**: Supports custom data acquisition workflows, which are adaptable and can integrate computer vision feedback mechanisms for enhanced functionality.
- **Threading and Parallelization**: To optimize performance, threading and parallelization techniques are extensively utilized, allowing for efficient handling of large objects and data processing.
- **Tree Data Structure**: The system's backbone for alignment, imaging, and image analysis is a reconfigurable tree data structure. This enables the creation of customizable acquisition "recipes" tailored to specific specimens.
- **Image Analysis Routines**: Custom routines for image analysis can also be loaded into **navigate** during run-time. Image analysis is performed on images in memory that are stored as numpy arrays, ensuring rapid processing.

Feature Lists
============================

Feature lists are highly versatile, capable of:

- **Sequential Execution**: Acquisition routes can be executed in a predefined order, ensuring systematic data collection.
- **Logic Gates Integration**: Incorporates conditional logic (e.g., if/then, try/except) and loop structures (while, for-loops), providing flexibility in data acquisition and processing.
- **Non-Imaging Processes**: Supports the inclusion of non-imaging-based processes, such as solvent exchange, broadening the application scope of the system.

Microscope Objects
============================

**navigate** supports the definition of multiple microscope objects, which can be configured in the `configuration.yaml` file. Each microscope object:

- **Independent or Shared Hardware**: Can have its own independent hardware or share hardware components with other microscope instances, providing flexibility in system design.
- **Multi-Modal Imaging**: Enables seamless definition of multi-modal imaging systems, allowing for integration of different imaging modalities within the same workflow.
- **Custom Acquisition Routines**: Supports the creation of distinct image acquisition routines for each microscope object, which can be switched dynamically as part of larger feature workflows or biological event handling.

This architecture allows for highly adaptable and reconfigurable imaging systems tailored to complex experimental needs.

