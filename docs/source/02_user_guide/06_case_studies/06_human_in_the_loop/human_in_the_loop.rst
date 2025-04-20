.. _human_in_the_loop:

====================================
Human-in-the-Loop Multiscale Imaging
====================================

Human-in-the-Loop multiscale imaging in *navigate* allows users to manually select regions of interest at low magnification, and then automatically revisit and image those regions at higher magnification with an alternative microscope configuration. This workflow is ideal for targeted analysis of biologically relevant features that may not be automatically detected, and gives the user direct control over which areas are imaged in detail.

This guide provides a step-by-step overview of how to set up and perform human-guided, multi-resolution imaging by creating a **NavigateMultipos** feature.

----------------------------

1. **Manually Mark Regions of Interest**

   - In the desired magnification of the low-resolution imaging system, right-click in the display window to mark regions or cells of interest. A popup will appear with the option to  **Mark Position**.

   .. image:: images/Picture1.png
      :align: center

   - These positions will be added to the multiposition table and used for targeted imaging.

2. **Switch to the Target, High-Resolution Imaging Mode**

   - Change the microscope to the target, high-resolution imaging system.
   - Verify that the imaging parameters (e.g., zoom, illumination settings) are correct.

3. **Select the NavigateMultipos Feature**

    - From the **Features** menu, select **Customized**, and choose **NavigateMultipos**.

   .. image:: images/Picture2.png
      :align: center

   - Change the acquisition mode to **Customized**, and select **Acquire** to open the **Feature List Configuration Window**.

   .. image:: images/Picture3.png
      :align: center

   - If the feature is not available, you may need create your own version of the feature, which can be done by selecting the **Add New Feature** menu from the **Features** menu. This can be done by copying the following code into the **Feature Popup Window**. In this example, the microscope automatically switches back to the low-resolution imaging system upon completing the high-resolution imaging.

    .. code-block:: python

        [
            {"name": PrepareNextChannel, },
            [
                {"name": MoveToNextPositionInMultiPositionTable, "args": (
                    "Mesoscale","1x",None,),},
                {"name": ZStackAcquisition, "args": (
                    True,True,"test/test/test",False,),},
                {"name": LoopByCount, "args": (
                    "experiment.MicroscopeState.multiposition_count",),}
            ],
            {"name": ChangeResolution, "args": (
                "Mesoscale","1x",),},
        ]

|

4. **Press the MoveToNextPositionInMultiPositionTable button in the Feature List Configuration Window**:

   - This will open the **Feature Parameters** window, which is where you configure the **MoveToNextPositionInMultiPositionTable** feature. It includes the following entries:

        - **get_origin**: Set to ``True``. This instructs the system to acquire the Z-stack at the current stage location, instead of using a predefined global Z-stack setting.
        - **saving_flag**: Set to ``True``. This instructs the system to save the acquired Z-stack.
        - **saving_dir**: Set to the desired directory for saving the acquired Z-stacks.
        - **force_multiposition**: Set to ``False``. If ``True``, this will force the system to acquire a Z-stack at each position, even if the position is not marked in the multiposition table.

   .. image:: images/Picture4.png
      :align: center


   - Once you have configured the parameters, close the window to save the settings.

5. **Click ZStackAcquisition**

    - In the same Feature List Configuration Window window, click **ZStackAcquisition** to configure the Z-stack acquisition settings for each marked position.
    - Once you have configured the parameters, close the window to save the settings.

   .. image:: images/Picture5.png
      :align: center

6. **Start Human-in-the-Loop Imaging**

   - Click **Confirm** to begin acquisition.
   - The system will automatically move to each marked position and acquire a Z-stack at the selected high-resolution settings.

