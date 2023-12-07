Case Study: Setting up the Voodoo ASLM
======================================

#. Launch the software in synthetic hardware mode.
#. :menuselection:`File --> Open configuration files`
#. For all devices in the `hardware` and in the `microscope` keys, we changed `type` to `synthetic`.
#. Change the DAQ `type` to `NI` and verify it is working with an oscilloscope.
#. Change camera type to `HamamatsuOrca` and add the correct serial number (get it from the label on the camera or open DCAMConfigurator or HCImage).
#. Start the software, confirm the camera is grabbing frames.
#. Filter Wheel first (identify comport by going to device manager)
