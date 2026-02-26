.. _code_quality:

************
Code Quality
************

This page defines coding and testing standards for contributions to **navigate**.

Coding Style
============

Naming Conventions
------------------

We follow `PEP 8 <https://peps.python.org/pep-0008/>`_. Class names use ``CamelCase`` and variables/functions use ``lowercase_with_underscores``.

Type Hints
----------

Type hints are used throughout the code base. Add type hints to new methods and functions. If needed, see `PEP 484 <https://peps.python.org/pep-0484/>`_.

Docstrings
----------

Use `numpydoc formatting guidelines <https://numpydoc.readthedocs.io/en/latest/format.html>`_ for docstrings.

Documentation Compatibility
---------------------------

Use `Sphinx <https://www.sphinx-doc.org/en/master/>`_-compatible docstrings and formatting. For examples, see the `Sphinx NumPy docstring example <https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html>`_.

Formatting and Linting
======================

- Use `Black <https://black.readthedocs.io/>`_ for formatting.
- Use `Ruff <https://docs.astral.sh/ruff/>`_ for linting.
- Run both via :command:`pre-commit run --all-files` before opening a pull request.

In rare cases, a targeted ``# noqa`` is acceptable. For example:

.. code-block:: python

    from navigate.model.device_startup_functions import start_stage
    device_name = "stage"
    exec(
        f"self.{device_name} = start_{device_name}("
        "name, device_connection, configuration, i, is_synthetic)"
    )

.. code-block:: python

    from navigate.model.device_startup_functions import start_stage  # noqa

Testing
=======

All new or changed behavior should include tests to prevent regressions and document expected behavior.

- We use `pytest <https://docs.pytest.org/en/7.2.x/>`_ for unit tests.
- Use existing tests in :file:`test/` as style examples.
- Run :command:`pytest` locally before submitting a pull request.

Configuration Dictionary Parsing
================================

The :ref:`configuration file <configuration_file>` is loaded as a large dictionary object. Use ``.get()`` with defaults where appropriate to reduce key errors and improve fallback behavior.

.. code-block:: python

    # Galvo waveform information
    self.galvo_waveform = self.device_config.get("waveform", "sawtooth")
