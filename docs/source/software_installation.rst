=====================
Software Installation
=====================

Computer Specifications
==================================================

**navigate** requires a robust computing environment for optimal performance.
Below are the recommended specifications:

Operating System Compatibility
------------------------------

.. important::
   The **navigate** software is primarily developed for use on Windows-based systems. This is due to the compatibility of device drivers for various microscope hardware components, such as cameras, stages, and data acquisition cards, which are predominantly designed for the Windows environment.

   While it is possible to launch the software on a Mac using a synthetic hardware mode, users should be aware of known issues with the Tkinter user interface. These issues include improper gridding of widgets and problems with resizing the GUI window. As such, the use of **navigate** software on macOS is not recommended.

   The software remains untested on Linux systems. Therefore, we cannot guarantee its functionality or performance on Linux platforms at this time. Users considering the use of **navigate** software on Linux should proceed with caution and be prepared for potential compatibility issues, especially with respect to device drivers.

.. note::
   For optimal performance and compatibility, it is strongly recommended to run the **navigate** software on a Windows machine, adhering to the specified system specifications.

Hardware Considerations
-----------------------

.. note::
   The read/write speed of the operating system drive and data storage is crucial. The **navigate** software leverages pyramidal file formats, which require additional overhead for down-sampling operations. Coupled with the demands of larger sCMOS sensors, this necessitates robust CPU performance and rapid data saving capabilities to ensure efficient processing and storage of large datasets.


.. collapse:: Example Hardware Configuration

    - *Base Platform*
        - **Product Name**: `Colfax SX6300 Workstation <https://www.colfax-intl.com/workstations/sx6300>`_
        - **Colfax Part #**: CX-116263

    - *Primary and Secondary CPU*
        - **CPU Model**: Intel Xeon Silver 4215R
        - **Configuration**: 8 Cores / 16 Threads
        - **Frequency**: 3.2 GHz
        - **Cache**: 11 MB
        - **TDP**: 130W
        - **Memory Support**: 2400 MHz

    - *Memory*
        - **Type**: Registered ECC DDR4
        - **Speed**: 3200 MHz
        - **Configuration**: 16 GB per socket, 8 sockets per CPU
        - **Total RAM**: >64 GB (recommended)

    - *Operating System Drive*:
        - **Type**: M.2 NVMe SSD
        - **Model**: Micron 7450 Max
        - **Capacity**: 800 GB
        - **Endurance**: 3 DWPD

    - *Primary Data Drive*:
        - **Type**: NVMe SSD
        - **Model**: Samsung PM9A3
        - **Capacity**: 7.68 TB
        - **Interface**: U.2 Gen4

    - *Secondary Data Drive*:
        - **Type**: SATA HDD
        - **Model**: Seagate Exos X20
        - **Capacity**: 20 TB
        - **Speed**: 7200 RPM
        - **Cache**: 256 MB
        - **Interface**: SATA 6.0 Gb/s

    - *Video Card*
        - **Model**: PNY nVidia T1000
        - **Memory**: 4 GB
        - **Interface**: PCI Express

    - *Network Interface*
        - **Model**: Intel X710-T2L RJ45 Copper
        - **Type**: Dual Port 10GbE
        - **Interface**: PCI-E x 8

    .. note::
       The specifications listed are based on an example system configuration and can be adjusted based on specific needs and availability.

---------------------

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

    * ``conda``'s configuration file can be found at C:\\Users\\UserProfile\\.condarc
    * ``pip``'s configiguration file can be found at C:\\Users\\UserProfile\\pip\\pip.ini

* You can also try to set the proxy from within the Anaconda Prompt:
*  ``set https_proxy=http://username:password@proxy.example.com:8080``
*  ``set http_proxy=http://username:password@proxy.example.com:8080``
