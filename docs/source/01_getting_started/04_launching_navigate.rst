.. _launching_navigate:

==================
Launching Navigate
==================

First Launch (Recommended)
--------------------------

After installation, validate your setup by launching in synthetic hardware mode first:

.. code-block:: console

    navigate -sh

Once the software opens in synthetic mode, configure your hardware next. We recommend using the configurator:

.. code-block:: console

    navigate -c

Follow the quick setup checklist in :ref:`Configuring Navigate <configuring_navigate>`.

After hardware configuration is complete, launch navigate normally:

.. code-block:: console

    navigate

.. note::
   Use synthetic hardware mode whenever the computer is not connected to microscope hardware.

Launch by Installation Strategy
-------------------------------

Conda + PyPI
^^^^^^^^^^^^

If you followed :ref:`Conda + PyPI <install_conda_pypi>`:

.. code-block:: console

    conda activate navigate
    navigate -sh
    navigate

venv + PyPI
^^^^^^^^^^^

If you followed :ref:`venv + PyPI <install_venv_pypi>`:

.. code-block:: console

    # Windows (cmd/powershell)
    .venv\Scripts\activate

    # Linux/Mac
    source .venv/bin/activate

    navigate -sh
    navigate

Install from GitHub
^^^^^^^^^^^^^^^^^^^

If you followed :ref:`Install from GitHub <install_github_source>`, activate the environment where you installed **navigate**, then launch:

.. code-block:: console

    navigate -sh
    navigate

uv Installation
^^^^^^^^^^^^^^^

If you followed :ref:`uv Installation <install_uv>`:

.. code-block:: console

    # Activate the uv-created environment
    # Windows (cmd/powershell)
    .venv\Scripts\activate

    # Linux/Mac
    source .venv/bin/activate

    navigate -sh
    navigate

.. _command_line_arguments:

Command Line Arguments
----------------------

Run :command:`navigate --help` to see all available options.

Core arguments
^^^^^^^^^^^^^^

.. list-table:: Core command line arguments
   :header-rows: 1
   :widths: 24 76

   * - Argument
     - Description
   * - :command:`-h`, :command:`--help`
     - Show available command line arguments.
   * - :command:`-sh`, :command:`--synthetic-hardware`
     - Launch without attached hardware (recommended for first launch, testing, and setup).
   * - :command:`-c`, :command:`--configurator`
     - Open the configuration wizard for creating/editing hardware configuration files.

Additional useful arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^
These arguments are not typically used, but can be helpful for advanced users. For example, by pointing navigate to different configuration files, you can easily switch between microscopes without modifying the default files. More detail about these files, and their role in navigate, can be found in :ref:`Software Configuration <configuration_file>`. For a full list of arguments, run :command:`navigate --help`.

.. list-table:: Additional command line arguments
   :header-rows: 1
   :widths: 32 68

   * - Argument
     - Description
   * - :command:`-d`
     - Enable the debugging tool menu.
   * - :command:`--config-file PATH`
     - Use a non-default :file:`configuration.yml`.
   * - :command:`--gui-config-file PATH`
     - Use a non-default :file:`gui_config.yml`.
   * - :command:`--experiment-file PATH`
     - Use a non-default :file:`experiment.yml`.
   * - :command:`--waveform-constants-file PATH`
     - Use a non-default :file:`waveform_constants.yml`.
   * - :command:`--waveform-templates-file PATH`
     - Use a non-default :file:`waveform_templates.yml`.
   * - :command:`--rest-api-file PATH`
     - Use a non-default :file:`rest_api_config.yml`.
   * - :command:`--logging-config PATH`
     - Use a non-default :file:`logging.yml`.
   * - :command:`--multi-positions-file PATH`
     - Use a non-default :file:`multi_positions.yml`.

.. tip::
   If you are running Windows with Conda, you can create a desktop shortcut to **navigate** by right-clicking the Desktop, selecting :guilabel:`New`, then :guilabel:`Shortcut`, and entering ``%windir%\system32\cmd.exe "/c" C:\path\to\miniconda\Scripts\activate.bat navigate && navigate`` in the location field.
