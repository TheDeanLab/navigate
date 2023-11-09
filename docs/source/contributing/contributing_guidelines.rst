Contributing Guidelines
=======================

We welcome contributions in the form of bug reports, bug fixes, new features
and documentation. If you are contributing code, please create it in a fork or
branch separate from the main ``develop`` branch and then make a pull request
to the ``develop`` branch for code review. Some best practices for new code are
outlined below.

If you are considering refactoring part of the code, please reach prior to
starting this process. We are happy to bring you and this discussion to our
regular software development meeting.

General Principles
------------------
- We use a `model-view-controller architecture <https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`_.
  New functionality should keep this strong separation.
- Please do not create new variables in existing code unless absolutely
  necessary, especially in the ``configuration.yaml`` and ``experiment.yaml``
  files. A new variable is necessary only if no variable stores similar
  information or there is no way to use the most similar variable without
  disrupting another part of the code base.
- We are happy to discuss code refactors for improved clarity and speed.
  However, please do not modify something that is already working without
  discussing this with the software team in advance.
- All code that modifies microscope control behavior must be reviewed and tested on a
live system prior to merging into the ``develop`` branch.

Installation of Developer Dependencies
--------------------------------------
To install the developer dependencies, run the following command from within the ASLM
repository folder::

    conda activate ASLM
    pip install -e '.[dev]'

Coding Style
--------------
We follow the `PEP8 code style guide <https://peps.python.org/pep-0008/>`_.
All class names are written in ``CamelCase`` and all
variable names are ``lowercase_and_separated_by_underscores``.

Documentation
-------------
All classes and functions should have docstrings written in
`Numpydoc style <https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy
.html>`_ in a sphinx-compatible format. This allows us to automatically generate
documentation for the code base. Example documentation can be found :doc:`here
<sphinx_numpydoc>`

Pre-Commit Hooks
---------------
We leverage pre-commit workflows to enforce consistent code formatting. In some rare
cases, Ruff may complain about a line of code that is actually fine. For example, in the example code below,
Ruff complains that the start_stage class is imported but not used. However, it is actually used in as part of an `exec` statement::

        from aslm.model.device_startup_functions import start_stage
        device_name = stage
        exec(f"self.{device_name} = start_{device_name}(name, device_connection, configuration, i, is_synthetic)")

To avoid this error, you can add a `# noqa` comment to the end of the line to tell Ruff to ignore the error::

        from aslm.model.device_startup_functions import start_stage  # noqa

Dictionary Parsing
------------------
The configuration file is loaded a large dictionary object, and it is easy to have
small errors in it that can crash the program. To avoid this, when getting
properties from the configuration dictionary, it is best to use the `.get()` command,
which provides you with the opportunity to also have a default value should the key
provided not be found.  For example::

        # Galvo Waveform Information
         self.galvo_waveform = self.device_config.get("waveform", "sawtooth")

Here, we try to retrieve the `waveform` key from a the `self.device_config`
dictionary.  In the case that this key is not available, it then by default returns
`sawtooth`. If however the `waveform` key is found, it will provide the value
associated with it.

Unit Tests
----------
Each line of code is unit tested to ensure it behaves appropriately
and alert future coders to modifications that break expected functionality.
Guidelines for writing good unit tests can be found `here <https://stackoverflow.com/questions/61400/what-makes-a-good-unit-test>`_
and `here <https://medium.com/chris-nielsen/so-whats-a-good-unit-test-look-like-71f750333ac0>`_,
or see examples of other unit tests in this application's ``test`` folder. We
use the `pytest library <https://docs.pytest.org/en/7.2.x/>`_ to evaluate unit
tests.

Developing with a Mac
----------------------
Many of us in the lab have Apple products and use them for development.
However, there are some issues that you may encounter when developing on a Mac.
Below are some of the issues we have encountered and how to resolve them.

OSError::

    OSError: You tried to simultaneously open more SharedNDArrays than are
    allowed by your system!

This results from a limitation in the number of shared memory objects that can
be created on a Mac. To figure out how many objects can open, open a terminal and
run the following command::

    ulimit -n

To increase this number, simply add an integer value after it. In our hands, a factor
of ~1000 typically works::

    ulimit -n 1000
