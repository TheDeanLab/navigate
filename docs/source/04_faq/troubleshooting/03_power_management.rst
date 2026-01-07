.. _power_management:

Computer Power Management and Firmware Configuration
====================================================

Why this matters
----------------

Navigate can drive sustained high data rates (camera readout, storage I/O, network transfer)
while also running CPU- and memory-intensive processing. On modern platforms, the *host's*
power management configuration (Windows power plan, chipset/firmware drivers, and BIOS/UEFI
power features) can materially affect throughput, latency, and run-to-run stability.

In our experience, we have seen server-grade, high-performance systems perform surprisingly
poorly when configured with power-saving defaults (for example: deep CPU sleep states, package
C-states, or aggressive firmware-controlled power management). The symptoms are often subtle:
lower-than-expected FPS/throughput, increased jitter, inconsistent job runtimes, and
"mystery slowdowns" that disappear after correcting BIOS/OS power settings.

At a high level, the goal is to keep the platform in a *deterministic performance state*:

* OS power plan prioritizes performance (minimizes power saving).
* Chipset/management drivers are correctly installed (avoids missing firmware interfaces).
* BIOS/UEFI disables deep idle states that add wake-up latency (C-states), while leaving
  frequency scaling and turbo enabled (P-states + Turbo).

Protocol: Windows host configuration
------------------------------------

1. Update baseline software and firmware
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Ensure the system is on a supported Windows release (Windows 10/11 or Windows Server).
#. Apply your vendor's recommended BIOS/BMC/firmware updates (Supermicro/HPE/Dell/etc.).
#. Reboot after firmware updates.

2. Set Windows to a performance-focused power mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Recommended (general):** High performance (works broadly).
**Optional (where available):** Ultimate Performance (not present on all editions).

*Check the current scheme:*

.. code-block:: powershell

   powercfg /getactivescheme
   powercfg /list

*Set High performance (alias):*

.. code-block:: powershell

   powercfg /setactive SCHEME_MIN

*Optional: enable + set Ultimate Performance (if supported on your edition):*

.. code-block:: powershell

   powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
   powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61

**GUI validation (recommended):**
Control Panel → Power Options → select **High performance** (or **Ultimate Performance**).

**Additional Windows power knobs to set (AC power):**
Power Options → Change plan settings → Advanced power settings:

* Processor power management:
  * Minimum processor state (Plugged in) = **100%**
  * Maximum processor state (Plugged in) = **100%**
* PCI Express:
  * Link State Power Management = **Off**

3. Install chipset platform drivers (including Intel Management Engine)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Intel Management Engine (ME) is a chipset subsystem that provides platform management
capabilities independent of the OS; the Windows driver typically appears as the
**Intel Management Engine Interface (MEI)** device. Install the correct chipset drivers
first, then ME/MEI.

**Confirm MEI is installed:**
Device Manager → System devices → look for **Intel(R) Management Engine Interface**.

4. Optional Windows Update: CPU/chipset-related driver updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Windows can deliver additional driver updates through **Optional updates**. Although it is referred to as "optional", these updates often include important chipset, storage, and network drivers
that improve performance and stability.

Settings → Windows Update → Advanced options → Optional updates → Driver updates

Protocol: BIOS/UEFI configuration
---------------------------------

The exact BIOS menu paths vary by vendor and CPU generation, but the concepts are similar.

1. NUMA and Node Interleaving
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Disable Node Interleaving** - recommended for modern non-uniform memory access (NUMA)-aware Operating Systems.

.. important::
   Some platforms do not expose an explicit **Node Interleaving** toggle (or it is hidden
   when the platform defaults to NUMA mode). In that case, verify NUMA is active in the OS
   (multiple NUMA nodes visible) and proceed with the remaining power settings.

2. Power and idle-state controls (C-states, P-states)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These settings are commonly found under:

Advanced → Advanced CPU Configuration → Advanced Power Management Configuration

The intent is:

* Keep **Turbo + P-states enabled** (fast frequency scaling).
* Disable **deep core/package C-states** (avoid wake-up latency and jitter).
* Disable **autonomous hardware power management** (keep behavior deterministic).

Recommended BIOS settings (with 1-line descriptions)
----------------------------------------------------

.. list-table:: BIOS settings reference (performance mode)
   :header-rows: 1
   :widths: 28 18 54

   * - Setting (location)
     - Recommended
     - What it does (1 line)
   * - **CPU P State Control** (APM)
     -
     -
   * - AVX P1
     - Nominal
     - Controls the target performance state under heavy AVX; *Nominal* avoids extra down-binning beyond platform defaults.
   * - SpeedStep (P-states)
     - Enabled
     - Enables OS-managed frequency/voltage scaling (fast ramp-up without sleeping).
   * - EIST PSD Function
     - HW_ALL
     - Uses hardware assistance for P-state transitions across all cores for responsiveness.
   * - Turbo Mode
     - Enabled
     - Allows boosting above base frequency when power/thermals permit.
   * - **Hardware PM State Control** (APM)
     -
     -
   * - Hardware P-States (HWP)
     - Disabled
     - Prevents the CPU from autonomously selecting performance states (keeps policy deterministic).
   * - Autonomous PM
     - Disabled
     - Disables out-of-band autonomous power decisions that can introduce variability.
   * - **CPU C State Control** (APM)
     -
     -
   * - Enable Monitor MWAIT
     - Disabled
     - Disables MWAIT-based idle entry hints that can lead to deeper idle behavior.
   * - CPU C1 Auto Demotion
     - Disabled
     - Prevents automatic demotion from shallow idle (C1) into deeper C-states.
   * - CPU C6 Report
     - Disabled
     - Hides C6 from the OS, preventing deep core sleep selection.
   * - Enhanced Halt State (C1E)
     - Disabled
     - Disables C1E voltage/frequency drop behavior that can add wake latency/jitter.
   * - **Package C State Control** (APM)
     -
     -
   * - Package C State
     - Disabled
     - Prevents the entire socket/package from entering deep idle (high wake latency).
   * - Package C State Limit
     - C0/C1
     - Caps package idle to shallow states only (best for consistent multi-socket performance).

Validation and troubleshooting
-----------------------------

*Generate an energy report (helps spot platform power issues):*

.. code-block:: powershell

   powercfg /energy

*Verify the active scheme again:*

.. code-block:: powershell

   powercfg /getactivescheme

If performance is still lower than expected, re-check:

* BIOS: C-states (core + package) truly disabled / limited to C0/C1.
* Windows: power plan is High/Ultimate Performance and PCIe link state power management is Off.
* Drivers: chipset and MEI installed; vendor storage/NIC drivers installed if required.

References:
-----------------------

* Microsoft powercfg documentation:
  https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options

* Windows power and performance tuning (server guidance):
  https://learn.microsoft.com/en-us/windows-server/administration/performance-tuning/hardware/power/power-performance-tuning

* Windows Optional updates / driver delivery:
  https://support.microsoft.com/en-us/windows/automatically-get-recommended-and-updated-hardware-drivers-0549a8d9-4842-8acb-75fa-a6faadb62507
  https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/understanding-windows-update-automatic-and-optional-rules-for-driver-distribution

* Intel Management Engine overview:
  https://www.intel.com/content/www/us/en/support/articles/000008927/software/chipset-software.html

* C-state guidance (example vendor guidance for performance impact):
  https://edc.intel.com/content/www/us/en/design/products/ethernet/appnote-perf-tuning-guide-700-series-linux/%E2%80%8Bc-state-control/
  https://www.cisco.com/c/en/us/products/collateral/servers-unified-computing/ucs-c-series-rack-servers/bios-tuning-guide-ucs-m8-intel-xeon-wp.html

* Node interleaving background:
  https://frankdenneman.nl/2010/12/28/node-interleaving-enable-or-disable/

