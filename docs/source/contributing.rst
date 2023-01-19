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

General principles
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
- All code that modifies microscope control behavior must be tested on a live
  system prior to merging into the ``develop`` branch.

Coding style
--------------

- We follow the `PEP8 code style guide <https://peps.python.org/pep-0008/>`_.
  Most importantly, all class names are written in ``CamelCase`` and all
  variable names are ``lowercase_and_separated_by_underscores``.
- All classes and functions should have docstrings written in
  `Numpydoc style <https://numpydoc.readthedocs.io/en/latest/format.html>`_.
- We leverage pre-commit workflows to enforce consistent code formatting.
Installation is optional. Use this only if it helps you. You could alternatively install Ruff (linter) and
Black (code formatter) extensions in VSCode and have them do the work there. Whatever
To enable pre-commits on your machine, follow the directions below::

    conda activate ASLM
    pip install pre-commit
    cd /path/to/ASLM
    pre-commit install


Unit tests
----------
Ideally, each line of code is unit tested to ensure it behaves appropriately
and alert future coders to modifications that break expected functionality.
Guidelines for writing good unit tests can be found `here <https://stackoverflow.com/questions/61400/what-makes-a-good-unit-test>`_
and `here <https://medium.com/chris-nielsen/so-whats-a-good-unit-test-look-like-71f750333ac0>`_,
or see examples of other unit tests in this application's ``test`` folder. We
use the `pytest library <https://docs.pytest.org/en/7.2.x/>`_ to evaluate unit
tests.

Scientific Units
----------------
Deviations from this can occur where it is necessary to pass a different unit to a piece of hardware.

* Time - Milliseconds
* Distance - Micrometers
