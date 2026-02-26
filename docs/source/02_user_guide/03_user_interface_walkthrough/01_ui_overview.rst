===========
UI Overview
===========

The main interface is split into four persistent areas:

1. :ref:`Menu Bar <ui_menu_bar>` for file, microscope, stage, feature, plugin, and window actions.
2. :ref:`Acquisition Bar <ui_acquisition_bar>` for starting and stopping runs and selecting acquisition mode.
3. :ref:`Settings Notebooks <ui_settings_notebooks>` for channel, camera, stage, and multi-position setup.
4. :ref:`Display Notebooks <ui_waveform_settings>` and camera display tools for live image and waveform feedback.

Where To Configure Common Tasks
===============================

.. list-table::
   :header-rows: 1

   * - Task
     - Primary Location
   * - Select acquisition mode and start a run
     - :ref:`Acquisition Bar <ui_acquisition_bar>`
   * - Configure channels, stack range, and timepoints
     - :ref:`Channels Notebook <ui_channels_notebook>`
   * - Set sensor mode and ROI
     - :ref:`Camera Settings <ui_camera_settings>`
   * - Move stage and define positions
     - :ref:`Stage Control <stage_control_notebook>` and :ref:`Multi-Position <ui_multiposition>`
   * - Configure waveform parameters
     - :ref:`Waveform Parameters <ui_waveform_parameters>`
   * - Save metadata before acquisition
     - :ref:`File Saving Dialog <ui_file_save_dialog>`
   * - Build custom feature-based routines
     - :ref:`Features <ui_features_menu>` and :ref:`Reconfigurable Acquisitions Using Features <user_guide_features>`

UI Conventions
==============

1. Most notebooks can be right-clicked and popped out into separate windows.
2. Many values update hardware immediately when edited, especially stage position entries.
3. Some controls are intentionally disabled in synthetic or unconfigured hardware contexts.
