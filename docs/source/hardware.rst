Hardware Setup
==========

Data Acquisition Card
------------
We have used several different NI-based data acquisition cards to run the software. These include PCIe-6738, PXIe-6259, and PXIe-6733.

.. tip::

    To find the device pinouts for your NI-based data acquisition card, open up NI MAX, find the card under devices,
    right-click and select 'device pinouts'.

The most important aspect is to wire up the triggering properly. The software first calculates all of the analog and digital waveforms, creates the NI tasks, and then queues these waveforms on the data acquisition board.
Upon receipt of a trigger, all of the analog an digital tasks are delivered in parallel. This provides us with deterministic behavior on a per-frame basis, which is necessary for proper ASLM-style acquisitions. It does not
however provide us with deterministic behavior between image frames, and some jitter in timing is anticipated.

Configuration File
----------
Upon running the software the first time, a copy of the configuration file is created in ``/Users/<username>/AppData/Local/.ASLM/config`` on Windows-based machines, and in ``~/.ASLM/config`` on Mac and
Linux-based machines. All changes will need to be made to this file. The local copy avoids conflicts between different microscopes after pulling new changes on GitHub.

Directions
------------

- Identify the device name in NI MAX, and change it if you would like. Common names are ``Dev1``, ``Dev2``, etc. This name must correspond with the pinouts provided in the configuration file.
- Connect the `camera_trigger_out_line` to the External Trigger of the Hamamatsu Camera. Commonly, this is done with a
counter port, e.g., ``/PXI6259/ctr0``
- Connect the ``master_trigger_out_line`` to the ``trigger_source`` with a direct wire, commonly ``PXI6259/port0/line1`` and ``/PXI6259/PFI0``

.. note::

    For NI-based cards, port0/line1 is the equivalent of ``P0.1``.
    There are multiple pins for each PFIO, including source, out, gate, etc. You must use the out terminal.
