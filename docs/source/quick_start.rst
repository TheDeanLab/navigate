.. _Quick_Start_Guide:

=================================
Quick Start Guide
=================================

This quick start guide covers how to install **navigate**, launch it in synthetic hardware mode to
confirm it is working, and save an image to disk.

Installation
------------

1. Install Miniconda
   Download and install Miniconda from the `official website <https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links>`_.

2. Create and Activate Environment

   .. code-block:: console

      (base) conda create -n navigate python=3.9.7
      (base) conda activate navigate

3. Install **navigate**

   .. code-block:: console

      (navigate) pip install git+https://github.com/TheDeanLab/navigate.git

4. Launch **navigate** in the synthetic hardware mode. This will allow you to test its functionality without actual hardware.

    .. code-block:: console

      (navigate) navigate -sh


Saving an Image to Disk
-----------------------

To save an image to disk, follow these steps:

* Launch **navigate** in synthetic hardware mode as described above.

* On the :guilabel:`Acquire Bar`, make sure that the operation mode is set to "Continuous Scan".

* Press :guilabel:`Acquire` (:kbd:`ctrl + enter`) and confirm that a synthetic noise image is
  displayed in the :guilabel:`Camera View` window.

.. Note::
    At least one channel must be selected in the :guilabel:`Channel Settings` window, and all of the parameters
    (e.g., :guilabel:`Power`) in that row must be populated.

* In the :guilabel:`Stack Acquisition Settings window`, press the :guilabel:`Set Start Pos/Foc` button. This specifies the
  starting ``Z`` and ``F`` (e.g., Focus) positions for the stack acquisition.

* Select the :guilabel:`Stage Control` tab (:kbd:`ctrl + 3`), move the ``Z`` stage to the desired position (e.g., ``100`` μm),
  go back to the :guilabel:`Channels` tab (:kbd:`ctrl + 1`),
  and press the :guilabel:`Set End Pos/Foc` button. This specifies the ending ``Z`` and ``F`` positions for the stack acquisition.

* In the :guilabel:`Stack Acquisition Settings` frame, you can now adjust the step size, which determines the number of slices in a z-stack.

* In the :guilabel:`Timepoint Settings` window, select :guilabel:`Save Data` (:kbd:`ctrl + enter`).
  If the number of timepoints is set to ``1``, only a single stack will be acquired.

* Change the :guilabel:`Acquire Bar` to the "Z-Stack" mode, and press :guilabel:`Acquire` (:kbd:`ctrl + enter`).

* A :guilabel:`File Saving Dialog` popup window will appear.
    * With the exception of :guilabel:`Notes`, all fields must be populated. Any spaces in the fields will be replaced with an underscore.
    * :guilabel:`Notes` is saved with the metadata, and can be useful for describing the experiment.
    * :guilabel:`Solvent` is useful for tissue clearing experiments.
    * :guilabel:`File Type` can be set to :guilabel:`.TIFF`, :guilabel:`OME-TIFF`, :guilabel:`H5`, or :guilabel:`N5`. The
      latter two options are pyramidal file formats that are best used for large datasets and are immediately compatible with
      `BigDataViewer <https://imagej.net/plugins/bdv/>`_,
      `BigStitcher <https://imagej.net/plugins/bigstitcher/index>`_, and more.
    * Press :guilabel:`Acquire Data` to begin the acquisition.
    * Once complete, the data can be visualized using standard image processing software such as `Fiji <https://imagej.net/software/fiji/>`_.

.. image:: user_guide/images/save_dialog.png
    :align: center
    :alt: File Saving Dialog

