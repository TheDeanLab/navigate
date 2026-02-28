.. _coordinate_system:

============================
Microscope Coordinate System
============================

This section defines the coordinate-system conventions expected by
**navigate**.

Problem And Motivation
----------------------

Smart-acquisition routines assume all microscopes follow the same axis
conventions. In practice, rigs often differ in stage polarity and camera
orientation. To ensure consistent behavior across setups, **navigate** defines a
standard coordinate system for microscope configuration.

When these conventions are followed and flip flags are set correctly in
``configuration.yaml``:

- Stage movements are more intuitive and predictable.
- Camera image orientation aligns with stage movement.
- Multi-microscope configurations remain consistent.
- Smart-acquisition routines behave as expected.

Standard Light-Sheet Microscope
-------------------------------

For a standard light-sheet microscope with one illumination objective and one
detection objective, **navigate** uses the following axis definitions.

Axis Definitions
^^^^^^^^^^^^^^^^

The physical coordinate system is defined relative to microscope geometry.

- **Z-axis (Detection Axis)**: ``-z`` is toward the detection objective;
  ``+z`` is away from the detection objective.
- **Y-axis (Illumination Axis)**: ``-y`` is toward the illumination objective;
  ``+y`` is away from the illumination objective.
- **X-axis (Horizontal Axis)**: ``-x`` is toward the optical table; ``+x`` is
  away from the optical table.
- **F-axis (Focus Axis)**: ``-f`` moves the detection objective toward the
  chamber; ``+f`` moves the detection objective away from the chamber.
- **Theta-axis (Rotation Axis)**: ``-theta`` is counterclockwise rotation;
  ``+theta`` is clockwise rotation.

.. important::

   Negative moves are associated with higher collision risk. This convention
   helps operators quickly identify potentially dangerous directions.

Stage Configuration
^^^^^^^^^^^^^^^^^^^

Stage directionality is configured with stage flip flags.

Option 1: Edit ``configuration.yaml`` directly.

.. code-block:: yaml

   microscopes:
       microscope1:
           stage:
               hardware:
                   type: ASI
                   ...
               x_min: -10000
               x_max: 10000
               flip_x: False
               flip_y: False
               flip_z: False
               flip_f: False
               flip_theta: False
               ...

Changes to flip flags take effect after restarting **navigate**.

Option 2 (recommended): Configure through the GUI.

1. Launch **navigate**.
2. Go to :menuselection:`Settings --> Stage Control --> Advanced Stage Parameters`.
3. Toggle the axis flip checkboxes as needed.
4. Click :guilabel:`Apply` or :guilabel:`Save`.

Each ``flip_<axis>`` flag reverses stage direction for that axis.

.. tip::

   The GUI workflow is usually faster for setup because you can test movement
   immediately after each change.

Camera Configuration
^^^^^^^^^^^^^^^^^^^^

Depending on camera mounting and optical reflections, configure camera flip
flags for X and Y.

Option 1: Edit ``configuration.yaml`` directly.

.. code-block:: yaml

   microscopes:
       microscope1:
           camera:
               hardware:
                   type: HamamatsuOrca
                   ...
               flip_x: False
               flip_y: False
               ...

Option 2 (recommended): Configure through the GUI.

1. Launch **navigate**.
2. Go to :menuselection:`Settings --> Stage Control --> Advanced Camera Settings`.
3. Toggle X/Y flip checkboxes as needed.
4. Click :guilabel:`Save`.

.. tip::

   GUI changes to camera flip flags are visible on subsequent frames, which
   helps with rapid orientation checks.

Expected Image Behavior
^^^^^^^^^^^^^^^^^^^^^^^

Camera movement should appear consistent with stage movement:

- Pressing **+x** (right) makes the sample appear to move left.
- Pressing **+y** (up) makes the sample appear to move down.
- Pressing **-x** (left) makes the sample appear to move right.
- Pressing **-y** (down) makes the sample appear to move up.

This is equivalent to standard microscope behavior: moving the stage in one
direction shifts the image in the opposite direction.

.. note::

   If your image movement does not match this behavior, adjust ``flip_x`` and
   ``flip_y`` until movement is consistent.

Multi-Sided Microscope Variants
-------------------------------

For multi-directional variants (for example, dual-side illumination or
dual-view detection), movement conventions are defined relative to the primary
microscope instance.

Configuration Example
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   microscopes:
       Microscope1_Left_Illumination:
           stage:
               ...
           camera:
               ...
       Microscope2_Right_Illumination(Microscope1_Left_Illumination):
           camera:
               hardware:
                   type: HamamatsuFusion
                   ...
               flip_x: True
               flip_y: False
               ...

Coordinate System Behavior
^^^^^^^^^^^^^^^^^^^^^^^^^^

- The primary microscope establishes the coordinate system.
- Secondary microscopes inherit that coordinate system.
- Secondary microscopes may require different camera flip flags.
- Stage movements typically affect all microscopes that share a stage.
- Camera orientation should be calibrated per microscope view.

Common Scenarios
^^^^^^^^^^^^^^^^

- **Two-sided illumination**: both views share the same stage coordinate
  system; camera flip flags may differ between views.
- **Dual-view detection**: detection paths can include different optical
  elements; camera orientation should be calibrated to the primary coordinate
  system; F-axis behavior can differ by optical path.

.. tip::

   After configuring a multi-sided microscope, verify stage movement behavior
   while viewing all active cameras.

Oblique-Plane Microscopes
-------------------------

For oblique-plane microscopes, coordinate handling is more complex because
illumination and detection geometry is angled. Stage and image coordinates may
require additional transformations.

.. warning::

   Oblique-plane coordinate-system documentation is still under development.

Preliminary Considerations
^^^^^^^^^^^^^^^^^^^^^^^^^^

When configuring oblique-plane systems:

- Illumination/detection angle affects coordinate transforms.
- Physical stage motion may not map directly to intuitive image motion.
- Flip flags alone may not be sufficient.
- Advanced workflows may require custom transform matrices.

For assistance or the latest guidance, open an issue on the **navigate**
`GitHub repository <https://github.com/TheDeanLab/navigate/issues/new/choose>`_.
