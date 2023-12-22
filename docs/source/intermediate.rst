================================================
Write A Smart Acquisition Routine (Intermediate)
================================================

navigate's :doc:`feature container <contributing/feature_container>` enables us to
write acquisition routines on the fly by chainging existing 
:doc:`features <user_guide/features>` into lists.

The brackets ``[]`` create a sequence of events to run in the feature container. As a
simple test case, we can run a single feature

.. code-block:: python

    [{"name": PrepareNextChannel}]

This will set up the next color channel for acquisition and then take an image. The
feature is a 