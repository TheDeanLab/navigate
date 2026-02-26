=======================
Stage And Multiposition
=======================

.. _stage_control_notebook:

Stage Control
=============

.. image:: images/settings_stage.png
   :align: center
   :alt: Stage Control settings notebook.

The :guilabel:`Stage Control` notebook provides movement controls for ``X``, ``Y``, ``Z``, ``focus``, and ``Theta``, plus emergency stop and joystick controls.

.. note::

   Stage axes loaded as synthetic devices appear with disabled motion buttons.

.. _ui_stage_positions:

Stage Positions
---------------

Entry boxes display live stage coordinates. Editing a value moves that axis to the entered coordinate.

.. warning::

   Editing position values can move hardware immediately. Keep stage limits enabled and verify clearance before movement.

XY Movement
-----------

Arrow buttons move ``X`` and ``Y``. The center entry sets step size in microns.

Z Movement
----------

Controls ``Z`` movement and its step size.

Focus Movement
--------------

Controls ``focus`` movement and its step size.

Theta Movement
--------------

Controls ``Theta`` (rotation) movement and its step size.

Buttons
-------

1. :guilabel:`STOP` halts all stage axes.
2. :guilabel:`Enable Joystick` / :guilabel:`Disable Joystick` toggles software control ownership for mapped joystick axes.

.. tip::

   On large displays, right-click a notebook tab and choose :guilabel:`Popout Tab` to create a detached stage-control panel.

   .. image:: images/popout_right_click.png
      :align: center
      :alt: Right-click popout menu for notebook tabs.

   .. image:: images/popout_stage.png
      :align: center
      :alt: Stage control tab shown as a popup window.

.. _ui_multiposition:

Multi-Position
==============

.. image:: images/settings_multiposition.png
   :align: center
   :alt: Multi-Position settings notebook.

The :guilabel:`Multi-Position` notebook defines stage coordinates for tiled and multi-region acquisition.

Multi-Position Buttons
----------------------

1. :guilabel:`Launch Tiling Wizard`
2. :guilabel:`Eliminate Empty Positions` (currently unimplemented)
3. :guilabel:`Save Positions To Disk`
4. :guilabel:`Load Positions From Disk`

.. _ui_multiposition_table:

Multi-Position Table
--------------------

The table stores stage coordinates included in multi-position runs.

.. image:: images/multiposition_right_click.png
   :align: center
   :alt: Right-click menu in the Multi-Position table.

1. Double-click a row index to move the stage to that row.
2. Double-click a cell to edit a coordinate value.
3. Right-click a row index to insert, add, or delete positions.

.. _ui_multiposition_tiling_wizard:

Multi-Position Tiling Wizard
============================

.. image:: images/tiling_wizard.png
   :align: center
   :alt: Tiling wizard window.

The tiling wizard calculates tiled position grids from start/end coordinates, field-of-view size, and overlap.

1. Set axis start and end positions.
2. Confirm FOV distance and overlap.
3. Click :guilabel:`Populate Multi-Position Table`.
