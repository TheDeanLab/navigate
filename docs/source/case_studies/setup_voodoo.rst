Case Study: Setting up the Voodoo ASLM
======================================

#. Launch the software in synthetic hardware mode.
#. :menuselection:`File --> Open Configuration Files`
#. Open the `configuration.yaml` using your favorite IDE. If you change the name of the microscope, this also has to be done in the other config files.
#. After each change in `configuration.yaml` file, you will need to restart the software.
#. For all devices in the `hardware` and in the `microscope` keys, we changed `type` to `synthetic`.
#. Change the DAQ `type` to `NI` and verify it is working with an oscilloscope.
#. Need to connect the master-trigger_out_line to the trigger_source.
#. Change camera type to `HamamatsuOrca` and add the correct serial number (get it from the label on the camera or open DCAMConfigurator or HCImage).
#. Connect the data acquisition card to the Ext. Trigger on the camera. You can find the pinouts on the NI MAX Device Pinouts page.
#. Start the software, run the software in the continuous mode, confirm the camera is grabbing frames.
#. Filter Wheel first (identify comport by going to device manager). If you would like to at this time, feel free to provide the names of each filter.
#. Select multiple channels in the channel settings, run the software in the continuous mode and make sure that the filter wheel is changing.
#. Now do the lasers. Only implemented in mixed modulation mode currently. Change type to NI, go through and make sure that each laser fires. For OBIS lasers, requires that he lasers be started in a mixed modulation mode.
#. Voice coil. Do the same. If the COM port is needed, will need to figure that out. Only required for EquipmentSOlutions that is not configured by default to go into an analog control mode.
#. Galvos, whether linear or resonant.
#. Stages.
#. Configure GUI defaults.
