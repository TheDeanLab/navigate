=========
ASI Model
=========

.. _asi-model-section:

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
