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
2. The right panel includes :ref:`LUT <ui_lut>`, image metrics, and display mode controls.

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

1. Select :guilabel:`Gray`, :guilabel:`Gradient`, or :guilabel:`Rainbow` display LUT.
2. :guilabel:`Flip XY` transposes display axes.
3. :guilabel:`Autoscale` toggles automatic min/max display scaling.
4. :guilabel:`Min Counts` and :guilabel:`Max Counts` are used when autoscale is disabled.

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

MipRenderFrame
--------------

.. image:: ../../images/mip-render-frame.png
   :align: center
   :alt: MipRenderFrame in the MIP tab.

This frame controls MIP perspective and channel selection.

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
