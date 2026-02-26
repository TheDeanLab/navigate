.. _computer_considerations:
.. _Quick_Start_Guide:

=================================
Computer Considerations
=================================

**navigate** can be installed, opened, and developed on a mid-range laptop with at least 8 GB of RAM and a processor with two cores. For operating a microscope, however, a workstation or server-grade system is typically preferred because microscope control often requires multiple PCIe expansion cards (for example, DAQ, high-speed networking, and storage). Saving data at a reasonable rate will also require a fast SSD. The hardware configuration for an example microscope control machine is shown below.

.. important::
   Scientific cameras are capable of rapidly generating large amounts of high-resolution data. As such, the read/write speed of the data storage device is critical for smooth operation of the software. For example, for a standard Hamamatsu camera with a 2048 x 2048 sensor, operating at 16-bit depth and 20 frames per second, the data save rate is approximately ~167 MB/s. While such capabilities are well within the capabilities of modern SSDs, they are beyond the capabilities of most HDDs. Therefore, it is recommended to use a fast SSD for data saving operations.

.. important::
   Power and firmware settings are required for predictable runtime performance. Complete the :ref:`Required Power/Firmware Settings <required_power_firmware_settings>` checklist below, then follow :ref:`power_management` for full instructions and validation.

.. _required_power_firmware_settings:

Required Power/Firmware Settings
--------------------------------

Use this checklist before running production acquisitions:

#. Set the Windows power plan to ``High performance`` (or ``Ultimate Performance`` when available).
#. Under advanced power settings, set processor minimum and maximum states to ``100%`` and set PCIe Link State Power Management to ``Off``.
#. Install platform chipset drivers and verify ``Intel(R) Management Engine Interface`` is present (for Intel platforms).
#. Update BIOS/UEFI and system firmware to vendor-recommended versions.
#. In BIOS/UEFI, keep Turbo and P-states enabled, and disable deep core/package C-states (or limit package C-state to C0/C1).
#. Disable Node Interleaving where available to preserve NUMA-aware behavior.

For detailed steps, vendor caveats, and validation commands, see :ref:`power_management`.


Example Computer Configuration
-------------------------------

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
