=====================
Software Installation
=====================

Quick install
=============

**Setup your Python Environment**

Head over to the `miniconda website <https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links>`_
and install the appropriate version based on your operating system.

.. tip::

    It is also handy to have the `conda cheatsheet <https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf>`_
    open when first using miniconda to get accustomed to the commands available.

* Windows: Use the Windows taskbar search to find "Anaconda Prompt (Miniconda3)".
  Given how frequently you will use this, we recommend pinning it to your taskbar.
* Linux/Mac: Open a Terminal.

**Create a Python environment called navigate that uses Python version 3.9.7**

.. code-block:: console

    (base) MyComputer ~ $ conda create -n navigate python=3.9.7

**Activate the navigate environment**

.. code-block:: console

    (base) MyComputer ~ $ conda activate navigate

The active environment is shown in parentheses on the far-left.  Originally, we were in
the miniconda ``(base)`` environment. After activating the navigate environment, it
should now show ``(navigate)``.

**Intall navigate via pip**

.. code-block:: console

    (navigate) MyComputer ~ $ pip install git+https://github.com/TheDeanLab/navigate.git

**Run the Navigate software**

.. code-block:: console

    (navigate) MyComputer Navigate $ navigate

.. note::

    If you are running the software on a computer that does not have the appropriate
    hardware you will need to add  the flag ``-sh`` (``--synthetic-hardware``) after
    navigate.

    .. code-block:: console

        navigate -sh

After completing these steps you will only need to do the below to start the software
upon opening a new Anaconda prompt:

.. code-block:: console

    (base) MyComputer ~ $ conda activate navigate
    (navigate) MyComputer ~ $ navigate

.. note::

    If you are running Windows, you can create a desktop shortcut to navigate by
    right-clicking the Desktop, navigating to New and then Shortcut and entering
    ``%windir%\system32\cmd.exe "/c" C:\path\to\miniconda\Scripts\activate.bat navigate && navigate``
    into the location text box.


Developer install
=================

**Download Git**

If you do not have `Git already installed <https://git-scm.com/downloads>`_, you will
need to do so before downloading the repo. We also recommend installing
`GitHub Desktop <https://desktop.github.com/>`_ for a more user-friendly experience.

**Create a directory where the repository will be cloned**
    We recommend a path/location that is easy to find and access such as the your
    Desktop or Documents. Once the folder is created, we will want to change that
    to our working directory (e.g., ``cd``)

* Windows

  .. code-block:: console

      (navigate) C:\Users\Username> cd Desktop
      (navigate) C:\Users\Username\Desktop> mkdir Code
      (navigate) C:\users\Username\Desktop> cd Code

* Linux/Mac

  .. code-block:: console

      (navigate) MyComputer ~ $ mkdir ~/Desktop/Code
      (navigate) MyComputer ~ $ cd ~/Desktop/Code

**Clone the GitHub repository**

.. code-block:: console

    (navigate) C:\Users\Username\Code> $ git clone https://github.com/TheDeanLab/navigate.git

**Install the Navigate repository**

The last step requires you to change into the navigate directory and the install the repo as
an editable package locally on your machine.

.. code-block:: console

    (navigate) C:\Users\Username\Code> cd navigate
    (navigate) C:\Users\Username\Code\navigate> pip install -e .[dev]

.. note::

  If working in a ``zsh`` shell, e.g. on a modern macOS, add single quotes around the
  call: ``pip install -e '.[dev]'``.

Troubleshooting
===============

If running the software on campus at UTSW you may need to update some of your proxy
settings to allow ``pip``/ ``conda`` to install the proper packages.

* This can be done by going to Environment Variables for Windows, or another OS
  equivalent.
* Create the following new System Variables:
    * Variable = HTTP_PROXY; Value = http://proxy.swmed.edu:3128
    * Variable = HTTPS_PROXY; Value = http://proxy.swmed.edu:3128 (please see that
      they are both http, this is purposeful and not a typo)
* If you continue to have issues then change the value of Variable HTTPS_PROXY to
  https://proxy.swmed.edu:3128
* If you still have issues then you will need to create/update both configuration
  files for conda and pip to include proxy settings, if they are not in the paths
  below you will need to create them. This assumes a Windows perspective. Mac/Linux
  users will have different paths, they can be found online.
    *  ``conda``'s configuration file can be found at C:\\Users\\UserProfile\\.condarc
    *  ``pip``'s configiguration file can be found at C:\\Users\\UserProfile\\pip\\pip.ini
* You can also try to set the proxy from within the Anaconda Prompt:
*  ``set https_proxy=http://username:password@proxy.example.com:8080``
*  ``set http_proxy=http://username:password@proxy.example.com:8080``
