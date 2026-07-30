=====================
Software Installation
=====================

.. _software_installation:

Operating System Compatibility
------------------------------

.. important::
   **navigate** is developed for use on Windows-based systems. This is due to the compatibility of device drivers for various microscope hardware components, such as cameras, stages, and data acquisition cards, which are predominantly designed for the Windows environment. The software is only partially tested on MacOS and Linux systems. Users considering the use of **navigate** software on Linux should proceed with caution and be prepared for potential compatibility issues. For optimal performance and compatibility, it is strongly recommended to run **navigate** on a Windows machine.


Choose an Installation Strategy
-------------------------------

Use the table below to pick the install path that best matches your goal.

.. list-table:: Installation Paths
   :header-rows: 1
   :widths: 28 24 24 24

   * - Goal
     - Source
     - Environment
     - Recommended Path
   * - Most users, stable release
     - PyPI
     - Conda
     - :ref:`Conda + PyPI <install_conda_pypi>`
   * - Stable release without conda
     - PyPI
     - Python :command:`venv`
     - :ref:`venv + PyPI <install_venv_pypi>`
   * - Latest code or local development
     - GitHub
     - Conda or :command:`venv`
     - :ref:`Install from GitHub Source <install_github_source>`
   * - Fast Python environment workflow
     - PyPI or GitHub
     - :command:`uv`
     - :ref:`uv Installation <install_uv>`

.. important::
   Use one environment manager per environment (for example, either Conda, :command:`venv`, or :command:`uv`).

.. _install_conda_pypi:

Conda + PyPI
^^^^^^^^^^^^

This option is recommended for most users as it provides a stable release with the benefits of Conda's environment management.
1. Install Miniconda from the `official website <https://docs.conda.io/en/latest/miniconda.html>`_.
2. Open :guilabel:`Anaconda Prompt (Miniconda3)` on Windows, or a terminal on Linux/Mac.
3. Create and activate a Conda environment:

.. code-block:: console

    (base) conda create -n navigate python=3.9.7
    (base) conda activate navigate

4. Install the latest stable release from PyPI:

.. code-block:: console

    (navigate) pip install navigate-micro

.. _install_venv_pypi:

venv + PyPI
^^^^^^^^^^^^

1. Navigate to the folder where you want to create the environment:

.. code-block:: console

    # Windows (cmd/powershell)
    cd C:\path\to\your\workspace

    # Linux/Mac
    cd /path/to/your/workspace

2. Create and activate a Python virtual environment:

.. code-block:: console

    python -m venv .venv

    # Windows (cmd/powershell)
    .venv\Scripts\activate

    # Linux/Mac
    source .venv/bin/activate

3. Install from PyPI:

.. code-block:: console

    pip install navigate-micro

.. _install_github_source:

Install from GitHub
^^^^^^^^^^^^^^^^^^^

Use this path if you want the latest repository changes or intend to modify code.
If you are on Windows and do not have Git installed, install `Git for Windows <https://git-scm.com/install/windows>`_ first.

1. Clone the repository:

.. code-block:: console

    git clone https://github.com/TheDeanLab/navigate.git
    cd navigate

2. Create/activate an environment (Conda or :command:`venv`), then install from
   source. On Windows, use the constraint file matching the environment's
   Python version:

.. code-block:: console

    # Windows with Python 3.9
    pip install -c constraints/windows-py39.txt .

    # Windows with Python 3.10
    pip install -c constraints/windows-py310.txt .

    # Linux/Mac
    pip install .

For development dependencies, use:

.. code-block:: console

    # Windows with Python 3.9
    pip install -c constraints/windows-py39.txt -e ".[dev]"

    # Windows with Python 3.10
    pip install -c constraints/windows-py310.txt -e ".[dev]"

    # Linux/Mac
    pip install -e ".[dev]"

The Windows files are complete snapshots of environments that passed the test
suite. `pip constraints
<https://pip.pypa.io/en/stable/user_guide/#constraints-files>`_ control the
versions selected during installation without declaring every transitive
dependency in :file:`pyproject.toml`. Do not mix a Python 3.9 constraint with a
Python 3.10 environment.

For full contributor setup, see :doc:`Developer Install <../03_contributing/02_developer_install/02_developer_install>`.

.. _install_uv:

uv Installation (PyPI or GitHub)
--------------------------------

If you use :command:`uv`, you can manage environments and installs with the same workflow.

1. Install `uv <https://docs.astral.sh/uv/getting-started/installation/>`_.
2. Create and activate an environment:

.. code-block:: console

    uv venv --python 3.9.7

    # Windows (cmd/powershell)
    .venv\Scripts\activate

    # Linux/Mac
    source .venv/bin/activate

3. Install from PyPI:

.. code-block:: console

    uv pip install navigate-micro

Or install latest code directly from GitHub:

.. code-block:: console

    uv pip install git+https://github.com/TheDeanLab/navigate.git

Or from a local clone:

.. code-block:: console

    git clone https://github.com/TheDeanLab/navigate.git
    cd navigate
    uv pip install -e .

Once installed, you can proceed to :ref:`Launching navigate <launching_navigate>` to start using the software.
