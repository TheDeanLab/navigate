=====================
Software Installation
=====================

Computer Specifications
==================================================

Below are the recommended specifications for **navigate**.

Operating System Compatibility
------------------------------

.. important::
   **navigate** is developed for use on Windows-based systems. This is due to the
   compatibility of device drivers for various microscope hardware components, such
   as cameras, stages, and data acquisition cards, which are predominantly designed
   for the Windows environment.

   While it is possible to launch the software on a Mac using synthetic hardware mode,
   users should be aware of known issues with the Tkinter interface. These issues
   include improper positioning of widgets and problems with resizing the GUI window.
   As such, the use of **navigate** on MacOS is not recommended.

   The software is untested on Linux systems. Users considering the use of **navigate**
   software on Linux should proceed with caution and be prepared for potential
   compatibility issues, especially with respect to device drivers.

.. note::
   For optimal performance and compatibility, it is strongly recommended to run
   **navigate** on a Windows machine.

Hardware Considerations
-----------------------

**navigate** will run on a mid-range laptop with at least 8 GB of RAM and a processor
with two cores. Most of its operations are undemanding. Saving data at a reasonable
rate, however, will require an SSD. The hardware configuration for an example
microscope control machine is shown below.

.. important::
   Scientific cameras are capable of rapidly generating large amounts of high-resolution data.
   As such, the read/write speed of the data storage device is a critical for smooth operation
   of the software. For example, for a standard Hamamatsu camera with a 2048 x 2048 sensor,
   operating at 16-bit depth and 20 frames per second, the data save rate is approximately ~167 MB/s.
   While such capabilities are well within the capabilities of modern SSDs, they are beyond the
   capabilities of most HDDs. Therefore, it is recommended to use a fast SSD data saving operations.


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
       The specifications listed are based on an example system configuration and can
       be adjusted based on specific needs and availability.

---------------------

Quick install
=============

**Setup your Python Environment**

Head over to the `miniconda website <https://docs.conda.io/en/latest/miniconda.html>`_
and install the appropriate version based on your operating system.

.. tip::

    It is also handy to have the `conda cheatsheet <https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf>`_
    open when first using miniconda to get accustomed to the commands available.

* Windows: Use the Windows taskbar search to find ``Anaconda Prompt (Miniconda3)``.
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

**Install navigate via pip**

To install the latest stable release of **navigate**, run the following command:

.. code-block:: console

    (navigate) MyComputer ~ $ pip install navigate-micro

To install the bleeding edge version of **navigate**, run the following command:

.. code-block:: console

    (navigate) MyComputer ~ $ pip install git+https://github.com/TheDeanLab/navigate.git

**Run navigate software**

.. code-block:: console

    (navigate) MyComputer ~ $ navigate

.. note::

    If you are running the software on a computer that is not connected to microscope
    hardware, you can add the flag ``-sh`` (``--synthetic-hardware``) to launch the
    program:

    .. code-block:: console

        navigate -sh

Launching **navigate**
======================

Open an ``Anaconda Prompt (Miniconda3)`` and enter the following.

.. code-block:: console

    (base) conda activate navigate
    (navigate) navigate

.. tip::

    If you are running Windows, you can create a desktop shortcut to **navigate** by
    right-clicking the Desktop, navigating to New and then Shortcut and entering
    ``%windir%\system32\cmd.exe "/c" C:\path\to\miniconda\Scripts\activate.bat navigate && navigate``
    into the location text box.

    This provides a convenient executable shortcut to launch the software, which is
    advantageous for users who are not comfortable with the command line.


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

  If working in a ``zsh`` shell, e.g. on a modern MacOS, add single quotes around the
  call: ``pip install -e '.[dev]'``.

Troubleshooting
===============

If the software is run at an institution with a proxy, you may need to update your proxy
settings to allow ``pip`` and ``conda`` to install the proper packages.

* This can be done by going to Environment Variables for Windows, or another OS
  equivalent.
* Create the following new System Variables (please see that
      they are both http, this is purposeful and not a typo):

    * Variable = HTTP_PROXY; Value = http://proxy.your_university.edu:1234
    * Variable = HTTPS_PROXY; Value = http://proxy.your_university.edu:1234

* If you continue to have issues then change the value of Variable HTTPS_PROXY to
  https://proxy.your_university.edu:1234

* If you still have issues then you will need to create/update both configuration
  files for conda and pip to include proxy settings, if they are not in the paths
  below you will need to create them. This assumes a Windows perspective. Mac/Linux
  users will have different paths, they can be found online.

    * The ``conda`` configuration file can be found at C:\\Users\\UserProfile\\.condarc
    * The ``pip`` configuration file can be found at C:\\Users\\UserProfile\\pip\\pip.ini

* You can also try to set the proxy from within the Anaconda Prompt:
*  ``set https_proxy=http://username:password@proxy.example.com:8080``
*  ``set http_proxy=http://username:password@proxy.example.com:8080``
