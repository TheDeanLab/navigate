=================
Display Notebooks
=================

The display notebooks provide visual feedback for image and waveform data during acquisition.

Camera View
===========

.. image:: ../../images/CameraTab.png
   :align: center
   :alt: Camera View notebook.

The :guilabel:`Camera View` notebook shows the current image and display controls.

1. Left-clicking the image toggles crosshairs.
2. The right panel includes :guilabel:`Display Mode`, :ref:`LUT <ui_lut>`, image metrics, and image display controls.
3. Display updates are deferred when the tab is hidden, then refreshed with the newest frame when the view is visible again.

HistogramFrame
--------------

.. image:: ../../images/histogram-frame.png
   :align: center
   :alt: HistogramFrame in the Camera View tab.

This frame displays the current image intensity histogram.

.. _ui_lut:

IntensityFrame
--------------

.. image:: ../../images/intensity-frame.png
   :align: center
   :alt: IntensityFrame in the Camera View tab.

This frame now uses one compact LUT editor for both single-channel and multichannel workflows in both Camera and MIP tabs.

1. :guilabel:`Channel` selects which channel settings are being edited.
2. In :guilabel:`Single` mode, channel selection is fixed to :guilabel:`All` and disabled.
3. In :guilabel:`Overlay` mode (with multiple active channels), channel selection is enabled so each channel can be configured independently.
4. :guilabel:`LUT` uses ImageJ-style colors (:guilabel:`Green`, :guilabel:`Red`, :guilabel:`Magenta`, :guilabel:`Cyan`, :guilabel:`Yellow`, :guilabel:`Blue`, :guilabel:`Orange`, :guilabel:`Gray`).
5. :guilabel:`Visible` toggles channel contribution on/off.
6. :guilabel:`Alpha` controls per-channel opacity from 0 to 100%.
7. :guilabel:`Gamma` controls per-channel gamma from 0.0 to 2.0 (default 1.0).
8. :guilabel:`Autoscale` applies per-channel automatic min/max scaling.
9. :guilabel:`Min Counts` and :guilabel:`Max Counts` are used when autoscale is disabled.

MetricsFrame
------------

.. image:: ../../images/metrics-frame.png
   :align: center
   :alt: MetricsFrame in the Camera View tab.

1. :guilabel:`Frames to Avg` is currently a placeholder for averaging behavior.
2. :guilabel:`Image Max Counts` reports maximum image intensity.
3. :guilabel:`Channel` indicates which selected acquisition channel is being displayed.

RenderFrame
-----------

.. image:: ../../images/render-frame.png
   :align: center
   :alt: RenderFrame in the Camera View tab.

This frame switches between live and slice display modes.
When channel-aware LUT controls are active, the channel selection in this frame is disabled.

MipRenderFrame
--------------

.. image:: ../../images/mip-render-frame.png
   :align: center
   :alt: MipRenderFrame in the MIP tab.

This frame controls MIP perspective and channel selection.

1. :guilabel:`Perspective` provides :guilabel:`Multi`, :guilabel:`XY`, :guilabel:`ZY`, and :guilabel:`ZX` views.
2. In :guilabel:`Multi` perspective, the XY MIP is shown with YZ on the right and XZ on the bottom.
3. YZ and ZX views are rescaled from acquisition metadata so axial and lateral spacing display isotropically.

.. _ui_waveform_settings:

Waveform Settings
=================

.. image:: ../../images/waveform-plots-frame.png
   :align: center
   :alt: Waveform plot frame in the Waveforms tab.

WaveformPlotFrame
-----------------

This frame displays generated remote-focus and galvo waveforms. The dashed
vertical line indicates camera timing relative to waveform output.

WaveformSettingsFrame
---------------------

.. image:: ../../images/waveform-settings-frame.png
   :align: center
   :alt: WaveformSettingsFrame in the Waveforms tab.

1. :guilabel:`Sample Rate` controls DAQ sample frequency.
2. :guilabel:`Waveform Template` selects the active :ref:`waveform template <configure_waveform_templates>`.
