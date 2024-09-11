=====================
Example Feature Lists
=====================

Fairly complex imaging sequences can be created by chaining together multiple
features. Here are a few examples of feature lists that can be used to create custom
acquisition protocols.


Multi-Position Imaging with Automated Autofocus
------------------------------------------------

Large volumes are often acquired in a tiling format, where the sample is imaged at
multiple positions. In some cases, if the sample is not perfectly transparent, the focus
may need to be adjusted at each position. This can be done automatically using the
autofocus feature.
#. You can load customized functions in the software by selecting the menu

Here, we begin by moving to the first position of the multi-position table, then move to
the first z-position, measure the autofocus, set the F_Start position, move to the last
z-position, measure the autofocus, set the F_End position, and image the full z-stack
prior to moving to the next position in the multi-position table.

.. code-block:: python

    [
        {"name": PrepareNextChannel,},
        (
            {"name": MoveToNextPositionInMultiPositionTable,"args": (None,None,None,),},
            {"name": CalculateFocusRange,},
            {"name": ZStackAcquisition,"args": (True,True,"z-stack",),},
            {"name": WaitToContinue,},
            {"name": LoopByCount,"args": ("experiment.MicroscopeState.multiposition_count",),},
        ),
    ]


-----------

Time-Lapse Imaging with Automated Autofocus
--------------------------------------------

Time-lapse imaging is a common technique used to monitor changes in samples over time
. If you do not have a hardware solution for maintaining the focus of the specimen, a
common technique for maintaining the focus of a microscope is to intermittently measure
the focus using the image as a metric.

.. code-block:: python

    [
        (
            {"name": PrepareNextChannel, },
            (
                {"name": Snap, "args": (True,),},
                {"name": LoopByCount, "args": (10,),},
            ),
            {"name": LoopByCount, "args": (2,),},),
            {"name": PrepareNextChannel, },
            {"name": WaitToContinue, },
            (
                {"name": Autofocus, "args": ("stage","z",),},
                (
                    {"name": Snap, "args": (True,),},
                    {"name": LoopByCount, "args": (5,),},
                ),
                {"name": StackPause, "args": ("experiment.MicroscopeState.timepoints",),},
                {"name": LoopByCount, "args": (10,),},
            ),
        ),
    ]
