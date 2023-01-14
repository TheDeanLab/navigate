ASLM feature container
=========================

The ASLM **feature container** allows for reconfigurable acquisition and
analysis. The feature container runs a tree of **features**, where each
feature may perform a *signal* operation, where it modifies the state of
microscope hardware, a *data* operation, where it performs an analysis on
acquired image data, or both.

Once a feature is executed, any features dependent on this feature's execution
will execute (for example, move the stage, then snap a picture). Following
this, the next set of features in sequence will be executed.

Examples of some existing features include
``aslm.model.features.common_features.ZStackAcquisition``, which acquires a
z-stack, and ``aslm.model.features.autofocus.Autofocus``, which finds the
ideal plane of focus of a sample using a Discrete Cosine Transform.

The feature object
------------------

Each feature is an object that accepts a pointer to ``aslm.model.model`` in its
``__init__()``  arguments and contains a configuration dictionary that dictates
feature behavior in its ``__init__()`` function. A complete configuration
dictionary is shown below. As few or as many of these options can be specified
as needed.

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
- ``main`` entries dictate the primary operation of the feature, to be once per
  acqusition step
- ``end`` entries describe any closing operations that must be performed when
  exiting the node
- ``cleanup`` entries dictate what happens if the node fails. This is for
  failsafe controls such as ``turn off all lasers''

The ``node`` configuration dictionary contains general properties of feature
nodes. ``node_type`` can be ``one-step`` or ``multi-step``, the latter indicating
we have an ``init``, a ``main`` and an ``end``. ``device_related`` is set to
``True`` if we have a ``multi-step`` signal container. ``need_response`` is set
to true if the signal node waits on hardware (e.g. waits for a stage to confirm
it has indeed moved) before proceeding.

Each of the functions that are the value entries in ``self.config_table``
dictionaries are methods of the feature object.

Writing custom features
-----------------------

.. note::

    This section is still under development.
