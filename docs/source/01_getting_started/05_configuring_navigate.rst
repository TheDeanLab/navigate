.. _configuring_navigate:

====================
Configuring Navigate
====================

The :file:`configuration.yaml` file defines the hardware and microscope settings that
**navigate** loads at startup. By default, this file is saved locally at:

* Windows: :file:`C:\\Users\\Username\\AppData\\Local\\.navigate\\config`
* Mac/Linux: :file:`~/.navigate`

.. warning::
   The configuration file is delicate. A reliable strategy is to initially create
   a working configuration file using only Virtual Devices, and then iteratively
   replace Virtual Devices with real devices, validating each device as you go.
   This way, if you encounter an error, you can easily identify the source of
   the problem.
.. tip::
   If you have trouble locating :file:`configuration.yaml`, launch navigate in the synthetic hardware mode and select
   :menuselection:`File --> Open Configuration Files`.


Configuration Wizard
--------------------

1. Activate the same environment you used during installation.
2. Launch the configurator:

.. code-block:: console

    navigate -c

3. Choose :guilabel:`New Configuration` to create a new configuration file, or
   choose :guilabel:`Load Configuration` to modify an existing configuration file.
4. If needed, click :guilabel:`Add A Microscope` to create a microscope entry.
   Navigate can support multiple microscopes, with hardware shared amongst
   microscopes, or unique to a particular microscope.
5. In each hardware tab, the first column shows configuration entries (most are
   likely required), the middle column is where you select or enter values, and
   the far-right column shows explanatory text.
6. Fill in required fields for each hardware tab (for example, DAQ, camera,
   stage, lasers, and filter wheel), validating one device at a time. Save the
   file as :file:`configuration.yaml` to your local navigate config directory.
7. Close the configurator and launch navigate:

.. code-block:: console

    navigate

.. image:: ../images/configurator.PNG
   :align: center
   :alt: Navigate configuration wizard window.

Advanced Configuration
----------------------
You can also manually edit :file:`configuration.yaml` to unlock advanced functionality.
For detailed explanations of all configuration sections, see
:ref:`Advanced Software Configuration <configuration_file>`.
