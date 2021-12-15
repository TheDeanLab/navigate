# Axially Swept Light-Sheet Microscopy Project

[![Auto-Docker functionality testing CI](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/autodocker-ci.yml/badge.svg?branch=main)](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/autodocker-ci.yml)

[![Image building and testing CI](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/container-ci.yml/badge.svg)](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/container-ci.yml)

### Project Outline
Adopts an MVC architecture for microscope control. 
Includes key code contributions from a number of open-source projects, including:
* https://github.com/mesoSPIM/mesoSPIM-control
* https://github.com/bicarlsen/obis_laser_controller
* https://github.com/utsw-bicf/auto-docker/
* https://github.com/uetke/UUTrack


### Continuous Integration
Includes functionality from Auto-Docker for remote building and testing of Docker images from a Docker build file (Dockerfile) and a unit test file (unittest.yml). Allows users to build, test and maintain Docker images outside of firewalls, proxies and machine limitations. Additionally, it is a storage repository, and can act as a functional archive and version control for all your Dockerfile recipes (though not the images themselves). Pipeline was developed by BICF from funding provided by **Cancer Prevention and Research Institute of Texas (RP150596)**.

[![Auto-docker DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4555891.svg)](https://doi.org/10.5281/zenodo.4555891)

### Equipment
Laser source - Omicron LightHUB Ultra.  Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers.  561, which operates separately, requires the mixed modulation mode (Obis).
Sample Scanning System - L-509.20DG10.  Has a unidirectional repeatability of 100 nm, bidirectional repeatablility of 2 microns, and a minimum incremental motion of 100 nm.  This is borderline too coarse.

### Installation with Conda
* conda create -n ASLM python=3.7.11
* conda activate ASLM
* python -m pip install -r requirements.txt
* cd into the right damn folder
* python __main__.py

### Hardware Dependencies
* DLL for Dynamixel Servo Motor

### Software Overview
The software is started by launching __main__.py. This configures the path to the base and configuration directories,
starts the tkinter GUi, instantiates the controller, and then begins the main loop. The controller then:
* Builds the Model from the configuration yaml file.
* Starts the hardware (camera, stages, etc.)
* Starts the View
* Begins the callbacks to trace GUI events.  Any changes are updated in both the GUI and the model.

### Authors
Kevin Dean
Dax Collision
Sampath Rapuri
Andrew Jamieson
Xiaoding 'Annie' Wang