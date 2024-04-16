=======================
Contributing Guidelines
=======================

We welcome contributions in the form of bug reports, bug fixes, new features
and documentation. If you are contributing code, please create it in a fork and
branch separate from the main ``develop`` branch and then make a pull request
to the ``develop`` branch for code review. Some best practices for new code are
outlined below.

If you are considering refactoring part of the code, please reach out to us prior to
starting this process. We are happy to invite you to our regular software development
meeting.

-------------------

General Principles
==================

- We use a `model-view-controller architecture <https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`_.
  New functionality should keep this strong separation. More information can be found
  in the :doc:`software architecture <software_architecture>` section.
- Please do not create new configuration variables unless absolutely
  necessary, especially in the ``configuration.yaml`` and ``experiment.yaml``
  files. A new variable is necessary only if no variable stores similar
  information or there is no way to use the most similar variable without
  disrupting another part of the code base.
- We are happy to discuss code refactors for improved clarity and speed.
  However, please do not modify something that is already working without
  discussing this with the software team in advance.
- All code that modifies microscope control behavior must be reviewed and tested on a
  live system prior to merging into the ``develop`` branch.

-------------------

Coding Style
============

We follow the `PEP8 code style guide <https://peps.python.org/pep-0008/>`_.
All class names are written in ``CamelCase`` and all
variable names are ``lowercase_and_separated_by_underscores``.

-------------------

Communicating with Hardware
===========================

In handling hardware devices, such as Sutter's MP-285A stage, using threads can introduce
complexities, especially when simultaneous read and write operations occur over a
shared resource like a serial line. An encountered issue demonstrated the challenges
when two different threads attempted to write to and read from the same serial port
simultaneously. This action led to data corruption due to interleaving of
read/write calls that require precise handshaking, characteristic of the MP-285A's
communication protocol. The solution involved implementing a blocking mechanism using
`threading.Event()` to ensure that operations on the serial port do not overlap,
showcasing the difficulties of multithreading sequential processes. To mitigate such
issues, a design where each hardware device operates within its own dedicated thread is
advisable. This approach simplifies the management of device communications by enforcing
sequential execution, eliminating the need to handle complex concurrency issues inherent
in multithreading environments. This strategy ensures robust and error-free interaction
with hardware devices.

-------------------


Documentation
=============

We use `Sphinx <https://www.sphinx-doc.org/en/master/>`_ to generate
documentation from documented methods, attributes, and classes. Please document
all new methods, attributes, and classes using a Sphinx compatible version of
`Numpydoc <https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html>`_.

-------------------

Scientific Units
================

Please express quantities in the following units when they are in the standard model/
view/controller code. Deviations from this can occur where it is necessary to pass a
different unit to a piece of hardware.

* Time - Milliseconds
* Distance - Micrometers
* Voltage - Volts
* Rotation - Degrees

-------------------

Pre-Commit Hooks
================

We use `pre-commit hooks <https://pre-commit.com/>`_ to enforce consistent code
formatting and automate some of the code review process. In some rare cases, the
linter may complain about a line of code that is actually fine. For example, in
the example code below, Ruff linter complains that the start_stage class is
imported but not used. However, it is actually used in as part of an
``exec`` statement.

.. code-block:: python

        from navigate.model.device_startup_functions import start_stage
        device_name = stage
        exec(f"self.{device_name} = start_{device_name}(name, device_connection, configuration, i, is_synthetic)")

To avoid this error, add a ``# noqa`` comment to the end of the line to tell Ruff to ignore the error.

.. code-block:: python

        from navigate.model.device_startup_functions import start_stage  # noqa

-------------------

Dictionary Parsing
==================

The :doc:`configuration file </user_guide/software_configuration>` is loaded as a
large dictionary object, and it is easy to create small errors in the dictionary that
can crash the program. To avoid this, when getting properties from the configuration
dictionary, it is best to use the ``.get()`` command, which provides you with the
opportunity to also have a default value should the key provided not be found. For
example,

.. code-block:: python

        # Galvo Waveform Information
        self.galvo_waveform = self.device_config.get("waveform", "sawtooth")

Here, we try to retrieve the ``waveform`` key from a the ``self.device_config``
dictionary.  In the case that this key is not available, it then by default returns
``sawtooth``. If however the ``waveform`` key is found, it will provide the value
associated with it.

-------------------

Unit Tests
==========

Each line of code is unit tested to ensure it behaves appropriately
and alert future coders to modifications that break expected functionality.
Guidelines for writing good unit tests can be found `here <https://stackoverflow.com/questions/61400/what-makes-a-good-unit-test>`_
and `over here <https://medium.com/chris-nielsen/so-whats-a-good-unit-test-look-like-71f750333ac0>`_,
or in examples of unit tests in this repository's ``test`` folder. We
use the `pytest library <https://docs.pytest.org/en/7.2.x/>`_ to evaluate unit
tests. Please check that unit tests pass on your machine before making a pull request.

-------------------

Developing with a Mac
=====================

Many of us have Apple products and use them for development.
However, there are some issues that you may encounter when developing on a Mac.
Below are some of the issues we have encountered and how to resolve them.

-------------------

Shared memory limits
^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  OSError: You tried to simultaneously open more SharedNDArrays than are
  allowed by your system!

This results from a limitation in the number of shared memory objects that can
be created on a Mac. To figure out how many objects can open, open a terminal and
run the following command

.. code-block:: console

  ulimit -n

To increase this number, simply add an integer value after it. In our hands, 1000
typically works:

.. code-block:: console

  ulimit -n 1000
