.. _contributing_guidelines:

************************
Contributing Guidelines
************************

We welcome contributions in the form of bug reports, bug fixes, new features, and documentation updates.

Contribution Policy
===================

All contributions should align with the core engineering direction of **navigate**:

- Keep a clear model-view-controller separation. See :ref:`software architecture <software-architecture-section>`.
- Minimize new dependencies when possible.
- Avoid unnecessary configuration variables in :file:`configuration.yaml` and :file:`experiment.yaml`.
- Discuss major refactors with the software team before implementation.
- For microscope-control behavior changes, require live-system validation before merge into ``develop``.
- Use standard units in model/view/controller code:

  - Time: milliseconds
  - Distance: micrometers
  - Voltage: volts
  - Rotation: degrees

Contribution Workflow
=====================

For setup and submission mechanics (forking, cloning, environment setup, branch creation, and pull requests), follow :ref:`Developer Install <developer_install>`.

PR Quality Bar
==============

Before opening a pull request, complete all required checks:

#. Run formatting and linting: :command:`pre-commit run --all-files`
#. Run tests: :command:`pytest`
#. If documentation changed, run: :command:`conda run -n navigate make -C docs html -j 15`
#. Add or update tests for new or changed behavior
#. Update documentation for user-facing or developer-facing changes

Code and Testing Standards
==========================

For coding style, type hints, docstring standards, linting/formatting policy, and testing guidance, see :ref:`Code Quality <code_quality>`.

Hardware Integration Guidance
=============================

For hardware concurrency, blocking communication patterns, and device interface requirements, see :ref:`Hardware Communication Guidelines <hardware_communication_guidelines>`.

Where To Ask For Help
=====================

- Open a general issue: `GitHub Issues <https://github.com/TheDeanLab/navigate/issues>`_
- Submit a bug report: `Issue report template <https://github.com/TheDeanLab/navigate/issues/new?template=issue-report.md>`_
- Submit a feature request: `Feature request template <https://github.com/TheDeanLab/navigate/issues/new?template=feature_request.md>`_

Contributor Behavior
====================

All contributors are expected to follow the :ref:`Code of Conduct <code_of_conduct>`.

.. toctree::
   :maxdepth: 1
   :hidden:

   code_quality
   code_of_conduct
