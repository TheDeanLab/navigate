.. _obis_tiger_connection:

Intermittent USB Connectivity
=============================

Overview
--------

For setups that include **Coherent OBIS lasers** and an **ASI Tiger Controller**, some users have reported intermittent serial/USB connection issues. These issues were first observed at CU Boulder and appeared to involve COM port conflicts.

Reported Issues
---------------

1. **Intermittent ASI stage connection failure**

   - Error example: ``Unable to connect to the serial port: Access to the port 'COM13' is denied.``
   - This was observed in both ASI/Tiger software and **navigate**.

2. **Errors in navigate logs**

   - Example log entry: ``model - ERROR - asi: ASI stage connection failed``.

3. **Unstable stage behavior during imaging**

   - In some runs, the stage connected but then moved sporadically during acquisition.

Suspected Cause
---------------

The issue appeared to be port competition between the Coherent OBIS laser and the ASI Tiger controller.

- ASI Tiger controller: **COM13**
- Coherent OBIS 561 nm laser (initial): **COM14**

Despite this assignment, the laser intermittently attempted to use COM13, displacing Tiger access and causing conflicts.

Solution and Verification
-------------------------

1. Reassigned the Coherent OBIS laser from COM14 to **COM9**.
2. Rebooted both the computer and hardware so the new port assignments were applied.

Results
-------

After reassigning the OBIS laser to COM9, the ASI stage remained stable on COM13 with no recurring connection interruptions or uncontrolled stage movement.
