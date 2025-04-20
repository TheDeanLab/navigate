
.. _obis_tiger_connection:

Intermittent USB Connectivity
===============================

Overview
--------
For setups that include **Coherent OBIS lasers** and an **ASI Tiger Controller**, some users have reported intermittent connection issues. These errors were first observed at CU Boulder, where the Coherent OBIS laser and the ASI Tiger controller appeared to experience conflicts over COM port assignments.

Reported Issues
---------------
1. **Connection Failure with the ASI Stage**:

   - The ASI stage intermittently fails to connect, with an error message reading: "Unable to connect to the serial port: Access to the port ‘COM13’ is denied."
   - This error has occurred in both the Tiger control software and *navigate*.

2. **Error Logs in Navigate**:

   - In the navigate software, the error is logged as: `"model - ERROR - asi: ASI stage connection failed"`.

3. **Stage Malfunction During Imaging**:

   - When a connection was achieved, the ASI stages exhibited sporadic movements during image acquisition.

Suspected Cause
---------------
Upon investigation, the issue appeared to stem from **port competition** between the Coherent OBIS laser and the ASI Tiger controller. In this setup:

   - The ASI Tiger controller was assigned to **COM port 13**.
   - The Coherent OBIS 561 nm laser was initially assigned to **COM port 14**.

Despite this configuration, the Coherent OBIS laser intermittently attempted to connect through COM port 13, effectively displacing the ASI Tiger controller's access to the port and causing a conflict.

Solution and Verification
-------------------------
To address this issue, the following corrective actions were implemented:

1. **Reassigning the Coherent OBIS Laser**:

   - The Coherent OBIS laser was reassigned from COM port 14 to **COM port 9** to prevent interference with the ASI Tiger controller. This port was chosen since it was in close proximity to the other Coherent OBIS laser instances.

2. **System Reboot**:

    - Following the reassignment, both the computer and hardware were rebooted to ensure the new COM port configurations took effect.

Results
-------
Since reassigning the Coherent OBIS laser to COM port 9, the ASI stage has maintained a stable connection on COM port 13 without interruptions and uncontrolled stage movements are no longer occurring.
