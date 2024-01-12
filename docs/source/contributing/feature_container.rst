.. _features:

=================
Feature Container
=================

**navigate** includes a **feature container** that enables reconfigurable acquisition and
analysis workflows. The feature container runs a tree of **features**, where each
feature may perform a *signal* operation, which modifies the state of the
microscope's hardware, or a *data* operation, where it performs an analysis on
acquired image data, or both.

Once a feature is executed, any features dependent on this feature's execution
will execute (for example, move the stage, then snap a picture). Following
this, the next set of features in sequence will be executed.

Examples of some existing features include ``navigate.model.features.common_features.ZStackAcquisition``, which acquires a
z-stack, and ``navigate.model.features.autofocus.Autofocus``, which finds the
ideal plane of focus of a sample using a Discrete Cosine Transform.

-----------------

Currently Implemented Features
==============================

.. toctree::
   :maxdepth: 2

   ../_autosummary/navigate.model.features.adaptive_optics
   ../_autosummary/navigate.model.features.auto_tile_scan
   ../_autosummary/navigate.model.features.autofocus
   ../_autosummary/navigate.model.features.common_features
   ../_autosummary/navigate.model.features.cva_conpro
   ../_autosummary/navigate.model.features.image_writer
   ../_autosummary/navigate.model.features.remove_empty_tiles
   ../_autosummary/navigate.model.features.restful_features
   ../_autosummary/navigate.model.features.volume_search

-----------------

.. _feature_objects:

Feature Objects
===============

Each feature is an object that accepts a pointer to ``navigate.model.model`` in its
``__init__()``  arguments and contains a configuration dictionary that dictates
feature behavior in its ``__init__()`` function. A complete configuration
dictionary is shown below. As few or as many of these options can be specified
as needed. Each function is considered a leaf or node of the feature tree.

.. code-block:: python

    self.config_table = {'signal': {'init': self.pre_func_signal,
                                    'main': self.in_func_signal,
                                    'end': self.end_func_signal,
                                    'cleanup': self.cleanup_func_signal},
                             'data': {'init': self.pre_func_data,
                                      'main': self.in_func_data,
                                      'end': self.end_func_data,
                                      'cleanup': self.cleanup_func_data},
                             'node': {'node_type': 'multi-step',
                                      'device_related': True,
                                      'need_response': True },
                            }

Both ``signal`` and ``data`` configuration entries are themselves
dictionaries that can contain ``init``, ``main``, ``end`` and/or
``cleanup`` entries.

- ``init`` entries dictate pre-processing steps that must be run before the
  main function of the feature starts.
- ``main`` entries dictate the primary operation of the feature, and are run once per
  acquisition step. They return ``True`` if the acquisition should proceed and ``False``
  if the acquisition should be ended.
- ``end`` entries are run once per main function returning ``True``. They check if the
  acquisition should end, if we are at any boundary points of the ``main`` function
  (e.g. if we need to change positions in a multi-position z-stack acquisition),
  and describe any closing operations that must be performed when exiting the feature
- ``cleanup`` entries dictate what happens if the node fails. This is for
  failsafe controls such as "turn off all lasers".

The ``node`` configuration dictionary contains general properties of feature
nodes. ``node_type`` can be ``one-step`` or ``multi-step``, the latter indicating
we have an ``init``, a ``main`` and an ``end``. ``device_related`` is set to
``True`` if we have a ``multi-step`` signal container. ``need_response`` is set
to true if the signal node waits on hardware (e.g. waits for a stage to confirm
it has indeed moved) before proceeding.

Each of the functions that are the value entries in ``self.config_table``
dictionaries are methods of the feature object.

-----------------

Creating A Custom Feature Object
--------------------------------

Each feature object is defined as a class. Creating a new feature is the same as
creating any Python class, but with a few requirements. The first parameter of the
``__init__`` function (after ``self``) must be ``model``, which gives the feature
object full access to the **navigate** model. All the other parameters are keyword
arguments and must have default values. The ``__init__`` function should always have a
``config_table`` attribute (see :ref:`above <feature_objects>` for a description of
the ``config_table``).

In the example below, we will create a custom feature that moves to a specified
position in **navigate**'s multi-position table and calculates the sharpness of the image
at this position using the Normalized DCT Shannon Entropy metric. An example
``__init__()`` function for our ``FeatureExample`` class is below.

.. code-block:: python

  from navigate.model.analysis.image_contrast import fast_normalized_dct_shannon_entropy

  class FeatureExample:

      def __init__(self, model, position_id=0):
          self.model = model
          self.position_id = position_id

          self.config_table = {
              "signal": {
                      "init": self.pre_func_signal,
                      "main": self.in_func_signal,
              },
              "data": {
                      "main": self.in_func_data,
              },
              "node": {
                  "device_related": True,
              }
          }

#. Get multi-position table position from the GUI.

   All the GUI parameters are stored in ``model.configuration["experiment"]`` during
   runtime. Below, we create a function to get all the position stored at
   ``position_id`` from the multi-position table in the GUI when we launch our
   feature.

   .. code-block:: python

       def pre_func_signal(self):
           positions = self.model.configuration["experiment"]["MultiPositions"]
           if self.position_id < len(positions):
               self.target_position = positions[self.position_id]
           else:
               current_position = self.model.get_stage_position()
               self.target_position = dict([(axis[:-4], value) for axis, value in current_position.items()])

   More GUI parameters can be found in `experiment.yml <https://github.com/TheDeanLab/navigate/blob/develop/src/navigate/config/experiment.yml>`_

#. Use the stage to move to this position.

   Now, we move stage to the ``target_position`` we grabbed from the multi-position
   table.

   .. code-block:: python

       def in_func_signal(self):
           pos = dict([(f"{axis}_abs", value) for axis, value in self.target_position.items()])
           self.model.move_stage(pos, wait_until_done=True)


#. Take a picture and process the resulting image.

  In parallel with our signal function call, the camera will acquire an image.
  The image captured by the camera will be stored in the ``model`` ``data_buffer``.
  The ``data`` functions run after an image is  acquired. We add code to deal with
  this image in the ``"main"`` data function. Here, we calculate the Shannon entropy
  of the image.

  .. code-block:: python

        def in_func_data(self, frame_ids):
            for id in frame_ids:
                image = self.model.data_buffer[id]
                entropy = fast_normalized_dct_shannon_entropy(image,
                    psf_support_diameter_xy=3)
                print("entropy of image:", id, entropy)

Now, we've create a whole new feature and can use it as we wish.

How to interact with other devices
----------------------------------

We interact with all devices through ``self.model.active_microscope``.
Here is an example to open shutter:

.. code-block:: python

  self.model.active_microscope.shutter.open_shutter()


How to pause and resume data threads in the model
-------------------------------------------------

The image data acquired from the camera are handled in an independent thread. As such,
the *signal* and *data* operations by default run in parallel and do not block each
other. Sometimes, we want to be sure a device is ready or has moved. For example, in
``FeatureExample``, we have no guarantee that the stage finished moving before the
image was taken. The ``wait_until_done`` call only blocks the signal thread from
progressing before the stage finishes its move. To ensure the data thread also waits,
we need to pause the data thread until the stage is ready.

Here is an example of how we can pause and resume the data thread:

.. code-block:: python

  self.model.pause_data_thread()

  self.model.move_stage(pos, wait_until_done=True)
  # ...

  self.model.resume_data_thread()

We can of course replace ``self.model.move_stage(pos, wait_until_done=True)`` with
whatever task we want to wait for before resuming image acquisition.

Model functions can be found :doc:`in the API <../_autosummary/navigate.model.model.Model>`.

Custom Feature Lists
====================

The **navigate** software allows you to chain feature objects into lists to build
acquisition workflows.

Creating a Custom Feature List in Python
----------------------------------------

To create a customized feature list, follow these steps:

#. Import the necessary modules:

  .. code-block:: python

    from navigate.tools.decorators import FeatureList
    from navigate.model.features.feature_related_functions import *

  ``FeatureList`` is a decorator that registers the list of features.
  ``feature_related_functions`` contains convenience imports that allow us to call
  ``PrepareNextChannel`` instead of
  ``navigate.model.features.common_features.PrepareNextChannel``.
  This makes for more readable code.

#. Create the feature list.

  .. code-block:: python

    @FeatureList
    def feature_example():
        return [
            (
                {"name": PrepareNextChannel},
                {
                    "name": LoopByCount,
                    "args": ("experiment.MicroscopeState.selected_channels",),
                },
            )
        ]

  In this example, the feature list takes one image per selected channel in the GUI.
  ``PrepareNextChannel`` sets up the channel and ``LoopByCount`` call this setup once
  per selected channel.

#. Now, open **navigate**.
#. Go to the :guilabel:`Features` menu.


   .. image:: images/step_1.png


#. Import the customized feature. Select :guilabel:`Add Custom Feature List` from the
   :guilabel:`Features` menu. A dialog box will appear, allowing you to select the
   Python file containing your customized feature list function.


   .. image:: images/step_2.png


#. Choose the Python file containing your customized feature list function. **navigate**
   will load the specified feature list, making it available for use in your
   experiments and analyses. It will appear at the bottom of the :guilabel:`Features`
   menu.
