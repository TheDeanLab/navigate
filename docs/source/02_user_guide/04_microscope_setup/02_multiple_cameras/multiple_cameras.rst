================
Multiple Cameras
================

**navigate** supports multi-camera acquisition across shared or independent
microscope definitions.

Enabling Multi-Camera Operation
-------------------------------

Before launching **navigate**, confirm both cameras are recognized by the host
computer and receive the same external trigger from the data acquisition card.
See :ref:`camera_configuration` for hardware setup details.

1. Open :menuselection:`Microscope Configuration --> Configure Microscope`.

   .. image:: images/multi_cams_1.png
      :align: center
      :alt: Menu path to open Configure Microscope.

   A popup appears with available microscope configurations and hardware details.

   .. image:: images/multi_cams_2.png
      :width: 400px
      :align: center
      :alt: Configure Microscope popup listing microscope configurations.

   Each microscope entry has three configurable options.

   .. image:: images/multi_cams_3.png
      :width: 400px
      :align: center
      :alt: Per-microscope options shown in Configure Microscope.

2. Set :guilabel:`Primary Microscope` and :guilabel:`Additional Microscope`,
   then click :guilabel:`Confirm`.

   .. image:: images/multi_cams_4.png
      :width: 400px
      :align: center
      :alt: Primary and additional microscope selections.

3. Choose acquisition mode and click :guilabel:`Acquire` as usual.
   A popup window appears with images from the additional camera.

   .. image:: images/multi_cams_5.png
      :align: center
      :alt: Additional camera view popup during acquisition.

Disabling Multi-Camera Operation
--------------------------------

When finished with multi-camera acquisition, reset to single-camera mode.

1. Open :menuselection:`Microscope Configuration --> Configure Microscope`.

   .. image:: images/multi_cams_1.png
      :align: center
      :alt: Menu path to open Configure Microscope.

2. Set :guilabel:`Primary Microscope`, then set
   :guilabel:`Additional Microscope` to :guilabel:`Not Use`.
   Click :guilabel:`Confirm`.

   .. image:: images/multi_cams_9.png
      :width: 400px
      :align: center
      :alt: Configure Microscope popup with Additional Microscope set to Not Use.
