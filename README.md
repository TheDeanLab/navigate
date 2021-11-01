auto-docker
========================================

[![Auto-Docker functionality testing CI](https://github.com/utsw-bicf/auto-docker/actions/workflows/autodocker-ci.yml/badge.svg?branch=main)](https://github.com/utsw-bicf/auto-docker/actions/workflows/autodocker-ci.yml)
[![Image building and testing CI](https://github.com/utsw-bicf/auto-docker/actions/workflows/container-ci.yml/badge.svg)](https://github.com/utsw-bicf/auto-docker/actions/workflows/container-ci.yml)

[![Auto-docker DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4555891.svg)](https://doi.org/10.5281/zenodo.4555891)


This repository is a template repository of our automated Docker image builder.


Introduction
------------

The purpose of this system is the remote building and testing of Docker images from a Docker build file (Dockerfile) and a unit test file (unittest.yml). This system allows users to build, test and maintain Docker images outside of firewalls, proxies and machine limitations. Additionally, it is a storage repository, and can act as a functional archive and version control for all your Dockerfile recipes (though not the images themselves).

The repository is a general purpose template for creating new docker building instances, as detailed in [Wiki](https://github.com/utsw-bicf/auto-docker/wiki). See [Setup](https://github.com/utsw-bicf/auto-docker/wiki/Setup) for documentation on how to modify the repository for your use.

Feedback
========

If you experience any issues with the auto-docker or would like to contribute to its source code, please visit [`utsw-bicf/auto-docker`](https://github.com/utsw-bicf/auto-docker).

Please [open an issue](https://git.io/JtyFp) for questions related to auto-docker usage, bug reports, or general inquiries.

Contribution Guidelines
=======================
We try to manage the required tasks for auto-docker using GitHub issues; you probably came to this page when creating one.

If you'd like to write some code to improve auto-docker, the standard workflow is as follows:


1. Check that there isn't already an issue about your idea in the [issue tracker](https://git.io/JtyFp) to avoid duplicating work
    * If there isn't one already, please create one so that others know what you're working on
2. [Fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) the [`bicf-utsw/auto-docker`](https://github.com/utsw-bicf/auto-docker) to your GitHub account
3. Make the necessary changes / additions within your forked repository
4. Submit a Pull Request against the `develop` branch and wait for the code to be reviewed and merged

If you're not used to this workflow with git, you can start with some [docs from GitHub](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests) or even their [excellent `git` resources](https://try.github.io/).  


Credits
=======
This workflow was developed by [Bioinformatic Core Facility (BICF), Department of Bioinformatics](http://www.utsouthwestern.edu/labs/bioinformatics/)

PI
--
Venkat S. Malladi\
*Faculty Associate & Director*\
Bioinformatics Core Facility\
UT Southwestern Medical Center\
<a href="https://orcid.org/0000-0002-0144-0564" target="orcid.widget" rel="noopener noreferrer" style="vertical-align:top;"><img src="https://orcid.org/sites/default/files/images/orcid_16x16.png" style="width:1em;margin-right:.5em;" alt="ORCID iD icon">orcid.org/0000-0002-0144-0564</a>\
[venkat.malladi@utsouthwestern.edu](mailto:venkat.malladi@utsouthwestern.edu)

Developers
----------
Jonathan Gesell\
*Computational Biologist*\
Bioinformatics Core Facility\
UT Southwestern Medical Center\
<a href="https://orcid.org/0000-0001-5902-3299" target="orcid.widget" rel="noopener noreferrer" style="vertical-align:top;"><img src="https://orcid.org/sites/default/files/images/orcid_16x16.png" style="width:1em;margin-right:.5em;" alt="ORCID iD icon">orcid.org/0000-0001-5902-3299</a>\
[johnathan.gesell@utsouthwestern.edu](mailto:jonathn.gesell@utsouthwestern.edu)

Gervaise H. Henry\
*Computational Biologist*\
Department of Urology\
UT Southwestern Medical Center\
<a href="https://orcid.org/0000-0001-7772-9578" target="orcid.widget" rel="noopener noreferrer" style="vertical-align:top;"><img src="https://orcid.org/sites/default/files/images/orcid_16x16.png" style="width:1em;margin-right:.5em;" alt="ORCID iD icon">orcid.org/0000-0001-7772-9578</a>\
[gervaise.henry@utsouthwestern.edu](mailto:gervaise.henry@utsouthwestern.edu)



Please cite in publications: Pipeline was developed by BICF from funding provided by **Cancer Prevention and Research Institute of Texas (RP150596)**.
