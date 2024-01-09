===========================
Acquire an Image (Beginner)
===========================

This guide will describe how to acquire a single image and a z-stack using the
**navigate** software package. Please refer to :ref:`multiposition table <user_guide/gui_walkthrough:multiposition>` for imaging in a
multiposition format or :doc:`case studies <user_guide/case_studies/case_studies_home>` for specialized examples using device-specific
microscope configurations.

Launching the Software Package
==============================

Open Anaconda Prompt
--------------------

To start, you need to open the Anaconda Prompt. Follow these steps:

1. On Windows, click on the Start menu.
2. Type ``Anaconda Prompt`` into the search bar.
3. Click on the Anaconda Prompt application to open it.

.. note::
   Ensure that Anaconda is already installed on your system. If not, download and install it from the
   `Anaconda website <https://docs.conda.io/projects/miniconda/en/latest/>`_.

Activate Conda Environment
--------------------------

Once the Anaconda Prompt is open, activate the desired conda environment. By default,
the command prompt will open the base environment (as shown in parentheses). To activate **navigate** environment,
type the following command into the Anaconda command window and press :kbd:`Enter`

.. code-block:: bash

   (base) conda activate navigate

Launch the Software Package
---------------------------

After activating the environment, **navigate** should now be shown in parentheses. After you have already
:ref:`configured <user_guide/setup_microscope>`  **navigate**, you can launch it by typing the following command into the Anaconda command window:

.. code-block:: bash

   (navigate) navigate


The navigate software package will launch and the main window will appear.

.. image:: images/beginner/open-navigate.png

Configure the Channel Settings
=============================================

* Select the :guilabel:`Channels` tab, which is located on the left side of the main window.
* Under the :guilabel:`Channel Settings` section, select the number of channels needed for imaging. For each channel selected,
  you will need to configure the acquisition settings:
  .. image:: images/beginner/channel-selector.png

    * Select the appropriate :guilabel:`Laser` from the dropdown menu.
    * Select the appropriate :guilabel:`Power` for the laser.
    * Select the appropriate emission :guilabel:`Filter` from the dropdown menu.
      .. image:: images/beginner/channel-selector-filter.png

    * Specify the camera :guilabel:`Exp. Time (ms)`. A good default value is ``100`` or ``200`` ms.
    * Specify the :guilabel:`Interval` to be ``1.0``. While this feature is not currently implemented,
      future releases will allow users to image different channels at different time intervals.
    * Specify the :guilabel:`Defocus` to be ``0``. This feature allows you to adjust for chromatic aberrations
      that result in focal shifts between each imaging channel.

Acquire in a Continuous Scan Mode
=================================

* Select "Continuous Scan" in the dropdown next to the :guilabel:`Acquire` button in the Acquire Bar.

.. note::
    If multiple channels are selected, each channel will be imaged sequentially.

.. image:: images/beginner/continuous-scan-dropdown.png

* Press :guilabel:`Acquire`. This will launch a live acquisition mode.

    .. image:: images/beginner/continuous-scan-acquire.png

* Move the stage either via joystick or the :guilabel:`X Y movement` and/or :guilabel:`Z movement` controls under the
   :guilabel:`Stage Control` tab until the sample comes into view and is in focus with the camera.

    .. image:: images/beginner/stage-movement-panel.png

* If enabled in the hardware, use the :guilabel:`Focus Movement` controls to adjust the detection objective position relative to the camera to adjust the focus. Check :doc:`configuration settings <user_guide/software_configuration>` for more information.

* Press the :guilabel:`Stop` button in the acquisition bar to Stop Acquisition

    .. image:: images/beginner/stop-acquisition.png

Acquiring a Single Image
======================

* Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.

    .. image:: images/beginner/continuous-scan-sample.png

* Similar to loading and finding the sample, move the stage via joystick or the controls in the
   :guilabel:`Stage Control` tab to find the desired region of the sample to image.
* Once desired imaging region is found, Select the number of color channels needed imaging in the :guilabel:`Channel tab`
   under :guilabel: `Channel Settings`. Select the correct filter for each channel by
   using the dropdown menu after each channel under the :guilabel:`Filter`. (Note, if multiple channels are selected, channels will be acquired sequentially)
* Change the camera exposure time by changing number in the :guilabel:`Exp. Time (ms)` for
   each channel.
* Set :guilabel:`Interval` to be ``1.0`` for each channel.
* Set :guilabel:`Defocus` to be ``0`` for each channel.
* Select "Normal" in the :guilabel:`Readout Direction` dropdown menu under the :guilabel:`Camera Modes` section in the :guilabel:`Camera settings` tab to acquire all pixels at once. Select "Light-Sheet" if using a rolling shutter. Refer to :doc:`ASLM <user_guide/case_studies/setup_voodoo>` for more information.

    .. image:: images/beginner/sensor-mode.png

* Define an imaging region across the camera chip using the :guilabel:`Region of Interest Settings` section under the :guilabel:`Camera Settings` tab.

    .. image:: images/beginner/ROI-definition.png

* Check the :guilabel:`Save Data` box in the :guilabel:`Timepoint Settings` section under the :guilabel:`Channels` tab to save the acquired images. Check this box before acquiring data.

    .. image:: images/beginner/save-data.png

* Select "Single Acquisition" from the dropdown next to the :guilabel:`Acquire` button.

    .. image:: images/beginner/single-acquisition-dropdown.png

* Press :guilabel:`Acquire` to open dialog saving box

    .. image:: images/beginner/single-acquisition-acquire.png

* Enter the sample parameters, notes, location to save file, and filetype in the :guilabel:`File Saving Dialog` that pops up.

    .. image:: images/beginner/save-dialog-box.png

* Press :guilabel:`Acquire Data` to initiate acquisition. Acquisition will automatically stop once the image is acquired.

    .. image:: images/beginner/save-dialog-box-acquire.png


Acquiring a Z-Stack
=================

* Using the :guilabel:`Channels` in the :guilabel:`Channel Settings` section, under the :guilabel:`Channels` tab, select the desired laser for imaging.
* Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
* Using the :guilabel:`Stage Control`, go to the desired z-position in the sample.

    .. image:: images/beginner/stage-control-start-pos-zstack.png

* Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)`
   press :guilabel:`Set Start Pos`.

    .. image:: images/beginner/press-start-pos.png

* Using the :guilabel:`Stage Control`, go to a different z-position within the sample.

    .. image:: images/beginner/stage-control-end-pos-zstack.png

* Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)`
   press :guilabel:`Set End Pos`.

    .. image:: images/beginner/press-end-pos.png

* Make sure :guilabel:`Set Foc` is ``0`` for both the :guilabel:`Set Start Pos` and
   :guilabel:`End Pos`.  Check :doc:`configuration settings <user_guide/software_configuration>` for more information to determine if focus is enabled in hardware. Refer to :doc:`configuration settings <user_guide/case_studies/acquire_mesospimbt>` for how to acquire a z-stack if focus is enabled.

* Type the desired step size (units um) in the :guilabel:`Step Size` dialog box in
   :guilabel:`Stack Acquistion Settings (um)`. The minimum step size and step increments are defined in stage section in the :guilabel:`experiment.yaml` file. More information can be found in :doc:`configuration settings <user_guide/software_configuration>`

    .. image:: images/beginner/define-step-size.png

* Select the number of color channels needed imaging in the :guilabel:`Channel tab`
   under :guilabel: `Channel Settings`. Select the correct filter for each channel by
   using the dropdown menu after each channel under the :guilabel:`Filter`.
* Change the exposure time by changing number in the :guilabel:`Exp. Time (ms)` for
   each channel.
* Set :guilabel:`Interval` to be ``1.0`` for each channel.
* Set :guilabel:`Defocus` to be ``0`` for each channel.
* * Select "Normal" in the :guilabel:`Readout Direction` dropdown menu under the :guilabel:`Camera Modes` section in the :guilabel:`Camera settings` tab to acquire all pixels at once. Select "Light-Sheet" if using a rolling shutter. Refer to :doc:`ASLM <user_guide/case_studies/setup_voodoo>` for more information.
* Define an imaging region across the camera chip in the :guilabel:`Region of Interest Settings` section under the :guilabel:`Camera Settings` tab.
* If using multiple channels for imaging, Select either :guilabel:`Per Z` or :guilabel:`Per Stack` under :guilabel:`Laser Cycling Settings` in the :guilabel:`Stack Acquisition Settings (um)` section under the :guilabel:`Channels` tab. :guilabel:`Per Z` acquires each channel before moving the stage to a new position and :guilabel:`Per Stack` acquires all images in a stack acquistion for a single channel before moving the stage back to the start position and restarting acquistion for the subsequent channel until all channels are imaged.

    .. image:: images/beginner/laser-cycling-settings.png

* Check the :guilabel:`Save Data` box in the :guilabel:`Timepoint Settings` section under the :guilabel:`Channels` tab to save the acquired images. Check this box before acquiring data.
* Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button.

    .. image:: images/beginner/z-stack-acquisition.png

   Press :guilabel:`Acquire`.
* Enter the sample parameters, notes, location to save file, and filetype in the :guilabel:`File Saving Dialog` that pops up.
* Press :guilabel:`Acquire Data` to initiate acquisition. Acquisition will automatically stop once the image series is acquired.

Acquiring a Multi-Position Z-Stack
================================

* Please refer to the :ref:`multiposition table <user_guide/gui_walkthrough:multiposition>` documentation on how to image a multiposition z-stack.
