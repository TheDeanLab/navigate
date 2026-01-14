.. _coordinate_system:

============================
Microscope Coordinate System
============================

This section details the expected coordinate system conventions for **navigate**-controlled microscopes.

-----------------

Problem / Motivation
====================

Smart-acquisition routines assume every microscope shares the same axis conventions, but each rig currently has different stage polarities and camera orientations. To ensure consistent behavior across different microscope setups, **navigate** defines a standardized coordinate system that should be followed when configuring new microscopes.

By adhering to these conventions and properly configuring the flip flags in your ``configuration.yaml`` file, you can ensure that:

* Stage movements are intuitive and predictable
* Camera image orientation matches stage movements
* Multi-microscope configurations work correctly
* Smart-acquisition features function as expected

-----------------

Standard Light-Sheet Microscope
================================

For the standard light-sheet microscope, with a single illumination and detection objective, we define the following coordinate system:

Axis Definitions
----------------

The physical coordinate system is defined relative to the microscope geometry:

**Z-Axis (Detection Axis)**
  * **-z** is towards the detection objective
  * **+z** is away from the detection objective

**Y-Axis (Illumination Axis)**
  * **-y** is towards the illumination objective
  * **+y** is away from the illumination objective

**X-Axis (Horizontal Axis)**
  * **-x** is towards the optical table
  * **+x** is away from the optical table

**F-Axis (Focus Axis)**
  * **-f** moves the detection objective towards the chamber
  * **+f** moves the detection objective away from the chamber

**Theta-Axis (Rotation Axis)**
  * **-theta** is counter-clockwise rotation
  * **+theta** is clockwise rotation

.. important::

    **Negative moves are associated with an increased collision/crash risk.** This convention helps operators quickly identify potentially dangerous movements.

Stage Configuration
-------------------

This defines how the stages move in the physical coordinate system. To alter these conventions to match your specific hardware, you should configure the flip flags in your ``configuration.yaml`` file under the ``stage`` section for your microscope:

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

Each ``flip_<axis>`` flag reverses the direction of stage movement for that axis. Set these flags to ``True`` or ``False`` to ensure your stage movements follow the standard coordinate system defined above.

.. tip::

    You can also configure flip flags through the Advanced Stage Parameters popup in the GUI by navigating to :menuselection:`Settings --> Stage Control --> Advanced Stage Parameters`. Changes made through the GUI will be saved to your configuration file.

Camera Configuration
--------------------

Depending on how the camera is mounted and whether any mirrors are in the detection path, you also need to configure the camera flip flags for x and y. These are specified in the ``camera`` section of your ``configuration.yaml`` file:

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

Expected Image Behavior
-----------------------

In general, the image on the camera should move in a manner that is consistent with the stage movement:

* When you press the **+x button** (located on the right), the sample will appear to move to the **left** in the image (i.e., we are trying to look further to the right)
* When you press the **+y button** (up), the sample will appear to move **down** in the image
* When you press the **-x button** (left), the sample will appear to move to the **right** in the image
* When you press the **-y button** (down), the sample will appear to move **up** in the image

This behavior mimics looking through a microscope eyepiece: when you move the stage to the right, the sample appears to move left in your field of view.

.. note::

    Use the flip flags to ensure your camera orientation matches these expected behaviors. You may need to experiment with different combinations of ``flip_x`` and ``flip_y`` depending on your camera mounting and optical path.

-----------------

Multi-Sided Microscope Variants
================================

For multi-directional versions of a microscope (e.g., two-sided illumination or dual-view detection), the movements are always defined **relative to the primary microscope instance**.

Configuration Example
---------------------

When you have multiple microscopes defined in your ``configuration.yaml`` file, all movements are defined relative to the first microscope:

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
                flip_x: True  # May need to flip relative to primary
                flip_y: False
                ...

Coordinate System Behavior
--------------------------

* The **primary microscope** (first defined) establishes the coordinate system
* All **secondary microscopes** inherit this coordinate system
* Secondary microscopes may require different flip flags to maintain consistency with the primary coordinate system
* Stage movements affect all microscopes simultaneously (since they typically share the same stage)
* Camera orientations may differ between microscopes and should be configured independently

Common Scenarios
----------------

**Two-Sided Illumination**
  When imaging with two illumination objectives (e.g., left and right):

  * Both views share the same stage coordinate system
  * Camera flip flags may differ between the two views
  * The detection objective and stage movements remain the same

**Dual-View Detection**
  When imaging with two detection objectives:

  * Each detection path may have different optical elements
  * Camera orientations should be calibrated to match the primary coordinate system
  * F-axis movements may affect only one detection path (configure accordingly)

.. tip::

    After configuring a multi-sided microscope, test stage movements while viewing both cameras to ensure the image movements are consistent and intuitive across all views.

-----------------

Oblique-Plane Microscope
=========================

For oblique plane microscopes, the coordinate system becomes more complex due to the angled illumination and detection geometry. The relationship between stage movements and image coordinates is not orthogonal, requiring special consideration.

.. warning::

    **Oblique plane microscope coordinate system documentation is under development.** More detailed information will be provided in a future release.

Preliminary Considerations
--------------------------

When configuring an oblique plane microscope, consider the following:

* The angle between the illumination and detection objectives affects the coordinate transformation
* Stage movements in the physical coordinate system may require geometric transformations to achieve intuitive image movements
* The flip flags alone may not be sufficient to achieve the desired behavior
* Custom transformation matrices may be needed for advanced acquisition features

Stay Tuned
----------

We are actively developing comprehensive coordinate system support for oblique plane microscopes. If you are setting up an oblique plane microscope with **navigate**, please contact the development team for the latest guidance and beta features.

.. note::

    For questions or assistance with oblique plane microscope configuration, please create an issue on the **navigate** `GitHub repository <https://github.com/TheDeanLab/navigate/issues/new/choose>`_.
