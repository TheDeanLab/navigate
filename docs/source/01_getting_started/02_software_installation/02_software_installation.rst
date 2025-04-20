=====================
Software Installation
=====================

.. _software_installation:

Computer Specifications
=======================

Below are the recommended specifications for **navigate**.

Operating System Compatibility
------------------------------

.. important::
   **navigate** is developed for use on Windows-based systems. This is due to the compatibility of device drivers for various microscope hardware components, such as cameras, stages, and data acquisition cards, which are predominantly designed for the Windows environment. The software is only partially tested on MacOS and Linux systems. Users considering the use of **navigate** software on Linux should proceed with caution and be prepared for potential compatibility issues. For optimal performance and compatibility, it is strongly recommended to run **navigate** on a Windows machine.

.. _computer_considerations:

Computer Considerations
-----------------------

**navigate** will run on a mid-range laptop with at least 8 GB of RAM and a processor with two cores. Most of its operations are undemanding. Saving data at a reasonable rate, however, will require an SSD. The hardware configuration for an example microscope control machine is shown below.

.. important::
   Scientific cameras are capable of rapidly generating large amounts of high-resolution data. As such, the read/write speed of the data storage device is critical for smooth operation of the software. For example, for a standard Hamamatsu camera with a 2048 x 2048 sensor, operating at 16-bit depth and 20 frames per second, the data save rate is approximately ~167 MB/s. While such capabilities are well within the capabilities of modern SSDs, they are beyond the capabilities of most HDDs. Therefore, it is recommended to use a fast SSD for data saving operations.

.. collapse:: Example Computer Configuration

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

Head over to the `miniconda website <https://docs.conda.io/en/latest/miniconda.html>`_ and install the appropriate version based on your operating system.

.. tip::
    It is also handy to have the `conda cheatsheet <https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf>`_ open when first using miniconda to get accustomed to the commands available.

* Windows: Use the Windows taskbar search to find ``Anaconda Prompt (Miniconda3)``. Given how frequently you will use this, we recommend pinning it to your taskbar. * Linux/Mac: Open a Terminal.

**Create a Python environment called navigate that uses Python version 3.9.7**

.. code-block:: console

    (base) MyComputer ~ $ conda create -n navigate python=3.9.7

**Activate the navigate environment**

.. code-block:: console

    (base) MyComputer ~ $ conda activate navigate

The active environment is shown in parentheses on the far-left. Originally, we were in the miniconda ``(base)`` environment. After activating the navigate environment, it should now show ``(navigate)``.

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
    If you are running the software on a computer that is not connected to microscope hardware, you can add the flag ``-sh`` (``--synthetic-hardware``) to launch the program:

    .. code-block:: console

        navigate -sh

Launching **navigate**
======================

Open an ``Anaconda Prompt (Miniconda3)`` and enter the following.

.. code-block:: console

    (base) conda activate navigate
    (navigate) navigate

.. tip::
    If you are running Windows, you can create a desktop shortcut to **navigate** by right-clicking the Desktop, navigating to New and then Shortcut and entering ``%windir%\system32\cmd.exe "/c" C:\path\to\miniconda\Scripts\activate.bat navigate && navigate`` into the location text box.

    This provides a convenient executable shortcut to launch the software, which is advantageous for users who are not comfortable with the command line.
