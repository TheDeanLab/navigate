===========================
Acquire an Image (Beginner)
===========================

This guide will describe how to acquire a single image and a z-stack using the
**navigate** software package. 

Launching the Software Package
==============================

Open Anaconda Prompt
--------------------

To start, you need to open the Anaconda Prompt. Follow these steps:

1. On Windows, click on the Start menu.
2. Type ``Anaconda Prompt`` into the search bar.
3. Click on the Anaconda Prompt application to open it.

.. note::
   Ensure that Anaconda and **navigate** are already installed on your system.
   If not, please refer to our :ref:`Quick_Start_Guide` for more information.


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
:ref:`configured <user_guide/setup_microscope>`  **navigate**, you can launch it by typing the following
command into the Anaconda command window:

.. code-block:: bash

   (navigate) navigate


The **navigate** software package will launch and the main window will appear.

    .. image:: images/beginner/open-navigate.png
         :alt: Opening **navigate**.

-------------------------

Configure the Channel Settings
=============================================

* Select the :guilabel:`Channels` tab, which is located on the left side of the main window.
* Under the :guilabel:`Channel Settings` section, select the number of channels needed for imaging. For each channel selected,
  you will need to configure the acquisition settings:

    .. image:: images/beginner/channel-selector.png
      :alt: Channel settings in the **navigate** software package.

    * Select the appropriate :guilabel:`Laser` from the dropdown menu.
    * Select the appropriate :guilabel:`Power` for the laser.
    * Select the appropriate emission :guilabel:`Filter` from the dropdown menu.

    .. image:: images/beginner/channel-selector-filter.png
      :alt: Changing the emission filter in **navigate**.

    * Specify the camera :guilabel:`Exp. Time (ms)`. A good default value is ``100`` or ``200`` ms.
    * Specify the :guilabel:`Interval` to be ``1.0``. While this feature is not currently implemented,
      future releases will allow users to image different channels at different time intervals.
    * Specify the :guilabel:`Defocus` to be ``0``. This feature allows you to adjust for chromatic aberrations
      that result in focal shifts between each imaging channel.

-------------------------

Configure the Camera Settings
============================================
* Select the :guilabel:`Camera Settings` tab, which is located on the left side of the main window.

* For standard imaging applications, select :guilabel:`Normal` in the :guilabel:`Sensor Modes` dropdown menu within the :guilabel:`Camera Modes` section.

* If you are using the rolling shutter, select :guilabel:`Light-Sheet` and specify its :guilabel:`Readout Direction`
  and :guilabel:`Number of Pixels`.

    .. note::
        For more information on how to configure the rolling shutter
        for ASLM operation, please refer to :doc:`ASLM <user_guide/case_studies/setup_voodoo>`.

    .. image:: images/beginner/sensor-mode.png
       :alt: Changing the camera sensor mode in **navigate**.

* Choose the size of your camera's field of view.
    * Specify the :guilabel:`Region of Interest Settings` by entering the appropriate
      :guilabel:`Number of Pixels` for both the :guilabel:`Width` and :guilabel:`Height` values.
    * Alternatively, one can select from one of several default values in the :guilabel:`Default FOVs` section.

    .. note::
        The :guilabel:`FOV Dimensions (microns)` is automatically calculated based on the :guilabel:`Number of Pixels`
        and the `pixel_size` as specified in the `zoom` section of your your ``configuration.yaml`` file.

        .. code-block:: yaml

            zoom:
              pixel_size:
                20x: 0.325 # magnification, and pixel size in microns


    .. image:: images/beginner/ROI-definition.png
         :alt: Changing the camera region of interest in **navigate**.

.. note::
    If multiple channels are selected, each channel will be acquired with the same camera
    :guilabel:`Sensor Mode`, :guilabel:`Readout Direction`, and :guilabel:`Region of Interest Settings`.

-------------------------

Acquire in a Continuous Scan Mode
=================================

* Select "Continuous Scan" in the dropdown next to the :guilabel:`Acquire` button in the Acquire Bar.

    .. image:: images/beginner/continuous-scan-dropdown.png
         :alt: Selecting the continuous scan mode in **navigate**.

* Press :guilabel:`Acquire`. This will launch a live acquisition mode.

    .. note::
        If multiple channels are selected, each channel will be imaged sequentially.
        The order of imaging is determined by the order of the channels in the 
        :guilabel:`Channel Settings` section of the :guilabel:`Channels` tab.

    .. image:: images/beginner/continuous-scan-acquire.png
         :alt: Launching the continuous scan mode in **navigate**.

* Move the stage to identify the location of the sample.
    * Select the :guilabel:`Stage Control` tab, and use the graphical user interface to move the stage.
      This includes buttons for moving the stage in ``X``, ``Y``, ``Z``, ``F``, and ``Theta`` directions.
        * The step size for each axis can be adjusted with the spinbox next to each button.
        * For stages loaded in a synthetic mode, buttons will be disabled.
        * Absolute positions can be entered in the text boxes next to each button.
        * Check :doc:`configuration settings <user_guide/software_configuration>` for more information.
    * Use the manufacturer-provided joystick to position the sample.

    .. note::
         The axes for a light-sheet microscope vary in the literature. Here, we define
         the ``Y`` axis as the direction of the light-sheet propagation, the ``Z`` axis
         as the direction of the detection objective, and the ``X`` axis as the direction
         perpendicular to the light-sheet and detection objective axes.

         The ``F`` axis typically controls the position of the detection objective along
         the detection axis.

         The ``Theta`` axis typically controls the rotation of the sample.

    .. warning::
        One should always be careful when moving the stage.

        If the stage is moved too
        quickly, the sample and/or microscope may be damaged.

        We strongly recommend that
        you implement stage limits in your configuration file. Please refer to the
        :doc:`configuration settings <user_guide/software_configuration>` for more information.

    .. image:: images/beginner/stage-movement-panel.png
        :alt: Moving the stage in **navigate**.

* Press the :guilabel:`Stop` button in the acquisition bar to Stop Acquisition

    .. image:: images/beginner/stop-acquisition.png
        :alt: Stopping the continuous scan mode in **navigate**.

-------------------------

Acquiring a Single Image
=========================


* Check the :guilabel:`Save Data` box in the :guilabel:`Timepoint Settings` section
  under the :guilabel:`Channels` tab to save the acquired images. Check this box before acquiring data.

    .. image:: images/beginner/save-data.png
        :alt: Saving data in **navigate**.

* Select :guilabel:`Single Acquisition` from the dropdown next to the :guilabel:`Acquire` button.

    .. image:: images/beginner/single-acquisition-dropdown.png
        :alt: Selecting the single acquisition mode in **navigate**.

* Press :guilabel:`Acquire` to open the :guilabel:`File Saving Dialog` interface.
  Enter the sample parameters, notes, location to save file, and filetype in the
  :guilabel:`File Saving Dialog` that pops up.

    .. image:: images/beginner/save-dialog-box.png
        :alt: Saving data in **navigate**.

* Press :guilabel:`Acquire Data` to initiate acquisition. Acquisition will automatically
  stop once the image is acquired.

    .. note::
        Each acquisition will be saved in a separate folder (e.g., ``Cell01``, ``Cell02``, ...)
        within the directory specified in the :guilabel:`File Saving Dialog` interface.

        Data will not be overwritten between acquisitions.

    .. image:: images/beginner/save-dialog-box-acquire.png
        :alt: Saving data in **navigate**.

-------------------------

Acquiring a Z-Stack
===================

* Using the :guilabel:`Stage Control`, go to the desired z-position in the sample. Make
  sure that the sample is in focus. To use the autofocus feature, please refer to the
  :ref:`Autofocus Settings <user_guide/gui_walkthrough:autofocus settings>` for more information.

    .. image:: images/beginner/stage-control-start-pos-zstack.png
        :alt: Adjusting the stage position in **navigate**.

* Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquisition Settings (μm)`
  press :guilabel:`Set Start Pos`.

    .. image:: images/beginner/press-start-pos.png
        :alt: Adjusting the stage position in **navigate**.

* Using the :guilabel:`Stage Control`, go to a different z-position within the sample. Again,
  make sure that the sample is in focus.

    .. image:: images/beginner/stage-control-end-pos-zstack.png
        :alt: Adjusting the stage position in **navigate**.

* Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquisition Settings (μm)`
  press :guilabel:`Set End Pos`.

    .. image:: images/beginner/press-end-pos.png
        :alt: Adjusting the stage position in **navigate**.

    .. note::
        If there is a shift in ``F`` between the start and stop positions, the
        ``F`` axis will be ramped synchronously with ``Z`` to maintain focus.

        Check :doc:`configuration settings <user_guide/software_configuration>`
        for more information to determine if focus is enabled in hardware.

        Refer to :doc:`Imaging on a mesoSPIM BT <user_guide/case_studies/acquire_mesospimbt>`
        section for an example of how to acquire a z-stack with a focus ramp.

* Type the desired step size in microns in the :guilabel:`Step Size` dialog box in
  :guilabel:`Stack Acquisition Settings (μm)`.

    .. note::
        The minimum step size, and increment between steps, are graphical user interface
        defaults that are specified in the ``experiment.yaml`` file. More information can
        :doc:`configuration settings <user_guide/software_configuration>`

        .. code-block:: yaml

            gui:
              stack_acquisition:
                step_size:
                  min: 0.100
                  max: 1000
                  step: 0.1



    .. image:: images/beginner/define-step-size.png


* If using multiple channels for imaging, select either :guilabel:`Per Z` or
  :guilabel:`Per Stack` under :guilabel:`Laser Cycling Settings` in the
  :guilabel:`Stack Acquisition Settings (μm)` section under the :guilabel:`Channels` tab.

    * :guilabel:`Per Z` acquires each channel before moving the stage to a new position.

    * :guilabel:`Per Stack` acquires all images in a stack acquisition for a single channel before moving
      the stage back to the start position and restarting acquisition for the subsequent channel
      until all channels are imaged.

    .. image:: images/beginner/laser-cycling-settings.png

* Select :guilabel:`Z-Stack` from the dropdown next to the :guilabel:`Acquire` button.
  Press :guilabel:`Acquire`.

    .. image:: images/beginner/z-stack-acquisition.png

* Enter the sample parameters, notes, location to save file, and filetype in the :guilabel:`File Saving Dialog` that pops up.
* Press :guilabel:`Acquire Data` to initiate acquisition. Acquisition will automatically stop once the image series is acquired.
