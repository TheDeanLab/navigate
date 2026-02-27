=======================
Stage And Multiposition
=======================

.. _stage_control_notebook:

Stage Control
=============

.. image:: ../../images/stage-control-tab-frame.png
   :align: center
   :alt: Stage Control tab.

The :guilabel:`Stage Control` notebook provides movement controls for ``X``, ``Y``, ``Z``, ``focus``, and ``Theta``, plus emergency stop and joystick controls.

.. note::

   Stage axes loaded as synthetic devices appear with disabled motion buttons.

.. _ui_stage_positions:

Stage Positions
---------------

.. image:: ../../images/stage-positions-frame.png
   :align: center
   :alt: Stage Positions frame.

Entry boxes display live stage coordinates. Editing a value moves that axis to the entered coordinate.

.. warning::

   Editing position values can move hardware immediately. Keep stage limits enabled and verify clearance before movement.

XY Movement
-----------

.. image:: ../../images/stage-xy-movement-frame.png
   :align: center
   :alt: XY Movement frame.

Arrow buttons move ``X`` and ``Y``. The center entry sets step size in microns.

Z Movement
----------

.. image:: ../../images/stage-z-movement-frame.png
   :align: center
   :alt: Z Movement frame.

Controls ``Z`` movement and its step size.

Focus Movement
--------------

.. image:: ../../images/stage-focus-movement-frame.png
   :align: center
   :alt: Focus Movement frame.

Controls ``focus`` movement and its step size.

Theta Movement
--------------

.. image:: ../../images/stage-theta-movement-frame.png
   :align: center
   :alt: Theta Movement frame.

Controls ``Theta`` (rotation) movement and its step size.

Buttons
-------

.. image:: ../../images/stage-buttons-frame.png
   :align: center
   :alt: Stage movement interrupt and joystick controls.

1. :guilabel:`STOP` halts all stage axes.
2. :guilabel:`Enable Joystick` / :guilabel:`Disable Joystick` toggles software control ownership for mapped joystick axes.

.. tip::

   On large displays, right-click a notebook tab and choose :guilabel:`Popout Tab` to create a detached stage-control panel.

.. _ui_multiposition:

Multi-Position
==============

.. image:: ../../images/MultiPositionTab.png
   :align: center
   :alt: Multi-Position settings notebook.

The :guilabel:`Multi-Position` notebook defines stage coordinates for tiled and multi-region acquisition.

1. Double-click a row index to move the stage to that row.
2. Double-click a cell to edit a coordinate value.
3. Right-click a row index to insert, add, or delete positions.

.. _ui_multiposition_buttons:

Multi-Position Buttons
----------------------

.. image:: ../../images/multiposition-buttons-frame.png
   :align: center
   :alt: Multi-Position buttons frame.

1. :guilabel:`Launch Tiling Wizard` opens :ref:`ui_multiposition_tiling_wizard`.
2. :guilabel:`Eliminate Empty Positions` (currently unimplemented)
3. :guilabel:`Save Positions To Disk`
4. :guilabel:`Load Positions From Disk`

Popup details for the tiling workflow are documented in :ref:`ui_multiposition_tiling_wizard`.
