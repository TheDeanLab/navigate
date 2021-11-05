# Axially Swept Light-Sheet Microscopy Project

[![Auto-Docker functionality testing CI](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/autodocker-ci.yml/badge.svg?branch=main)](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/autodocker-ci.yml)
[![Image building and testing CI](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/container-ci.yml/badge.svg)](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/container-ci.yml)

### Project Outline
Adopts an MVC architecture for microscope control. Includes key code contributions from a number of open-source projects, including:
* https://github.com/mesoSPIM/mesoSPIM-control
* https://github.com/bicarlsen/obis_laser_controller
* *


### Continuous Integration
Includes functionality from Auto-Docker for remote building and testing of Docker images from a Docker build file (Dockerfile) and a unit test file (unittest.yml). Allows users to build, test and maintain Docker images outside of firewalls, proxies and machine limitations. Additionally, it is a storage repository, and can act as a functional archive and version control for all your Dockerfile recipes (though not the images themselves). Pipeline was developed by BICF from funding provided by **Cancer Prevention and Research Institute of Texas (RP150596)**.

[![Auto-docker DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4555891.svg)](https://doi.org/10.5281/zenodo.4555891)
