Developer Install
=================

The following sections provide detailed guidance for developers that wish to contribute to **navigate**. They aim to help you set up your development environment, effectively work with the codebase, and contribute to its growth.

* :ref:`Download and Install Git <download_git>`
* :ref:`Create Directory for Installation <create_directory>`
* :ref:`Fork Repository <fork_repository>`
* :ref:`Clone Repository <clone_repository>`
* :ref:`Install navigate in a Virtual Environment <virtual_environment>`


.. _download_git:

**Download Git**

If you do not have `Git already installed <https://git-scm.com/downloads>`_, you will need to do so before cloning the repo. We also recommend installing `GitHub Desktop <https://github.com/apps/desktop>`_ for a more user-friendly experience.

.. _create_directory:

**Create a directory where the repository will be cloned**

We recommend a path/location that is easy to find and access such as the your Desktop or Documents. Once the folder is created, we will want to change that to our working directory (e.g., ``cd``).

* Windows

  .. code-block:: console

      (navigate) C:\Users\Username> cd Desktop
      (navigate) C:\Users\Username\Desktop> mkdir Code
      (navigate) C:\users\Username\Desktop> cd Code

* Linux/Mac

  .. code-block:: console

      (navigate) MyComputer ~ $ mkdir ~/Desktop/Code
      (navigate) MyComputer ~ $ cd ~/Desktop/Code

.. _fork_repository:

**Working with a Fork**

For external contributors, we recommend forking the repository first. If you do not intend to contribute to the project, you can skip this step and clone the main repository directly.

1. Visit https://github.com/TheDeanLab/navigate and click the "Fork" button
2. Clone your fork instead of the main repository:

.. code-block:: console

    git clone https://github.com/YOUR-USERNAME/navigate.git
    cd navigate

3. Set up the upstream remote to keep your fork updated:

.. code-block:: console

    git remote add upstream https://github.com/TheDeanLab/navigate.git

4. Create a branch for your changes:

.. code-block:: console

    git checkout -b your-feature-branch

.. _clone_repository:

**Clone the GitHub repository**

For those who do not want to fork the repository, you can clone the main repository directly. This will create a local copy of the repository on your machine.

.. code-block:: console

    C:\Users\Username\Code> $ git clone https://github.com/TheDeanLab/navigate.git

.. _virtual_environment:

**Install navigate in a Virtual Environment**

We strongly recommend using a virtual environment for development. This can be accomplished either with Python's built-in `venv` or `conda`.

.. code-block:: console

    # Using venv
    python -m venv navigate-env

    # On Windows
    navigate-env\Scripts\activate

    # On Linux/Mac
    source navigate-env/bin/activate

    # Then install Navigate
    pip install -e .[dev]

The same thing can be achieved using conda:

.. code-block:: console

    # Using conda
    conda create -n navigate python=3.9.7
    conda activate navigate
    (navigate) C:\Users\Username\Code> cd navigate

    # On Windows
    (navigate) C:\Users\Username\Code\navigate> pip install -e .[dev]

    # On Linux/Mac
    (navigate) pip install -e '.[dev]'
