# Multiscale Axially Swept Light-Sheet Microscopy Project

[![Tests](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/push_checks.yaml/badge.svg)](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/push_checks.yaml)
[![codecov](https://codecov.io/gh/AdvancedImagingUTSW/ASLM/branch/develop/graph/badge.svg?token=270RFSZGG5)](https://codecov.io/gh/AdvancedImagingUTSW/ASLM)

### Project Philosophy
* Minimal number of dependencies. Prioritize standard library Python imports for maximum stability.
* Sufficiently generic that it can drive all of our microscopes, different camera types, etc.
* Brutally obvious and well documented so that it can be understood up with by future users years from now.
* Should resemble Danuser/Dean/Fiolka LabView software so that people do not have to relearn a new GUI for every microscope.  Maximize productivity for biological users.
* Must be high-performance and responsive.  Will implement threading approaches inspired by Andrew York's concurrency tools.
* Based upon the proven Model-View-Controller architecture.  

### Equipment
* Laser source - Omicron LightHUB Ultra.  Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers.  561, which operates separately, requires the mixed modulation mode (Obis).
* Sample Scanning System - L-509.20DG10.  Has a unidirectional repeatability of 100 nm, bidirectional repeatablility of 2 microns, and a minimum incremental motion of 100 nm.  This is borderline too coarse.
* GPUs - 2x NVIDIA Titan RTX with an NVLINK bridge - CUDA Architecture = 7.5, Driver Version = 456.71. 
* Camera - 2x Hamamatsu Flash 4.0 with framegrabbers.
* Remote Focusing Units - Optotune Electrotunable Lens for low-resolution imaging and a ThorLabs BLINK for high-resolution imaging.
* National Instruments PXIe-1073 Chassis equipped with PXI6733 and PXI6259 Data Acquisition Devices
* Filter Wheels - 2x 32mm High-Speed Filter Wheels

### GPU Dependencies for TensorFlow (1.15), PyTorch (1.10.2), CuPy, ...
Excellent directions can be found for CuPy. https://docs.cupy.dev/en/stable/install.html
 * [NVIDIA CUDA Version 11.2](https://developer.nvidia.com/cuda-11.2.0-download-archive?target_os=Windows&target_arch=x86_64&target_version=10&target_type=exelocal)
 * [cuDNN SDK 8.4.1](https://developer.nvidia.com/rdp/cudnn-download)
 * NVIDIA Graphics Driver >450.80.02
 * TensorRT 7
 * Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017 and 2019 
 
### Installation with Conda
~~~
conda create -n ASLM python=3.9.7
conda activate ASLM
python -m pip install --upgrade pip
mkdir ~/Git/
cd ~/Git/
git clone https://github.com/AdvancedImagingUTSW/ASLM.git
cd ASLM
pip install -e .
~~~

To run, enter `aslm` in the `ASLM` Anaconda environment.

### Trouble Shooting
If running the software on campus at UTSW you may need to update some of your proxy settings to allow pip/conda to install the proper packages.
* This can be done by going to Environment Variables for Windows, or another OS equivalent.
* Create the following variables at the system level: 
    Variable = HTTP_PROXY; Value = http://proxy.swmed.edu:3128
    Variable = HTTPS_PROXY; Value = http://proxy.swmed.edu:3128 (please see that they are both http, this is purposeful and not a typo)
* If you continue to have issues then change the value of Variable HTTPS_PROXY to https://proxy.swmed.edu:3128
* If you still have issues then you will need to create/update both configuration files for conda and pip to include proxy settings, if they are not in the paths below you will need to create them. This assumes a Windows perspective. Mac/Linux users will have different paths, they can be found online.
    Conda's Config file = C:\Users\UserProfile\.condarc
    Pip's Config file = C:\Users\UserProfile\pip\pip.ini
* You can also try to set the proxy from within the Anaconda Prompt:
	set https_proxy=http://username:password@proxy.example.com:8080
	set http_proxy=http://username:password@proxy.example.com:8080

### Hardware Dependencies
* DLL for Dynamixel Servo Motor

### Software Overview
The software is started by launching `main.py`. This configures the path to the base and configuration directories,
starts the tkinter GUi, instantiates the controller, and then begins the main loop. The controller then:
* Builds the Model from the configuration yaml file.
* Starts the hardware (camera, stages, etc.)
* Starts the View
* Begins the callbacks to trace GUI events.  Any changes are updated in both the GUI and the model.

![alt text](https://github.com/AdvancedImagingUTSW/ASLM/blob/develop/aslm_architecture.jpg?raw=true)

### Command Line Input Arguments (optional)
* --verbose: Verbose mode.
* --synthetic_hardware: Use simulated hardware.

~~~
python main.py --verbose --synthetic_hardware
~~~

### Authors
* Kevin Dean
* Zach Marin
* Xiaoding 'Annie' Wang
* Dax Collison
* Sampath Rapuri
* Samir Mamtani
* Renil Gupta
* Andrew Jamieson


Includes inspiration from a number of open-source projects, including:
* https://github.com/mesoSPIM/
* https://github.com/bicarlsen/obis_laser_controller
* https://github.com/uetke/UUTrack
* https://github.com/AndrewGYork/tools
