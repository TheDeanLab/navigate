# Axially Swept Light-Sheet Microscopy Project

### Project Outline
Adopts an MVC architecture for microscope control. 
Includes key inspiration and code contributions from a number of open-source projects, including:
* https://github.com/mesoSPIM/mesoSPIM-control
* https://github.com/bicarlsen/obis_laser_controller
* https://github.com/utsw-bicf/auto-docker/
* https://github.com/uetke/UUTrack
* https://github.com/MouseLand/cellpose/blob/master/README.md

### Project Philosophy
* Want to have a minimal amount of dependencies. Predominantly local Python imports for maximum stability.
* Want it to be sufficiently generic that it can drive all of our microscopes (with a few tweaks here and there), different camera types, etc.
* Want it to be brutally obvious and well documented so that it can be understood up with by future grad students, postdocs, etc., years from now.
* Want it to resemble Danuser/Dean/Fiolka LabView software, so that people do not have to relearn a new GUI for every microscope.  Maximize productivity for our more biological users.
* Want it to be performant.  Will implement Andrew York's concurrency tools.
* Want to adopt proven architectures, such as the Model-View-Controller architecture.  

### Equipment
* Laser source - Omicron LightHUB Ultra.  Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers.  561, which operates separately, requires the mixed modulation mode (Obis).
* Sample Scanning System - L-509.20DG10.  Has a unidirectional repeatability of 100 nm, bidirectional repeatablility of 2 microns, and a minimum incremental motion of 100 nm.  This is borderline too coarse.
* GPUs - 2x NVIDIA Titan RTX with an NVLINK bridge.  NVIDIA CUDA Version 11.5.1, cuTENSOR v1.3, cuDNN v8.3, and cuSPRASELt v0.10 installed on OS. THe NCCL v2.1 library is not yet available for Windows OS, but will potentially be valuable for multi-GPU support.
* Camera - 2x Hamamatsu Flash 4.0 with framegrabbers.
* Remote Focusing Units - Optotune Electrotunable Lens for low-resolution imaging and a ThorLabs BLINK for high-resolution imaging.

### Installation with Conda
~~~
conda create -n ASLM python=3.9.7
conda activate ASLM
python -m pip install -r requirements.txt
cd into the right damn folder (ex C:\Users\UserProfile\Documents\GitHub\ASLM\src\)
python main.py
~~~

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
* Dax Collison
* Sampath Rapuri
* Andrew Jamieson
* Xiaoding 'Annie' Wang
