
.. _navigate-home:

############
**navigate**
############


**navigate** is an open-source Python software for general microscope control. It focuses
on smart microscopy applications by providing reusable acquisition and analysis routines,
termed :ref:`features <features>`, that can be chained
in arbitrary orders to create custom acquisition protocols. **navigate** is designed to accommodate the needs of
a diverse user base, from biologists with no programming experience to advanced
technology developers.

.. note::

   This project is under active development. See our `GitHub repository for updates
   <https://github.com/TheDeanLab/navigate>`_.

**Project Philosophy**
=========================

* Minimal number of dependencies. Prioritize standard library imports for maximum stability.
* Abstraction layer to drive different camera types, etc.
* Brutally obvious, well-documented, clean code.
* Maximize productivity for biological users.
* Performant and responsive.
* Model-View-Controller architecture.

**Contents**
============

.. toctree::
   :caption: Getting Started
   :maxdepth: 2

   quick_start
   software_installation
   i_want_to

.. toctree::
   :caption: User Guide
   :maxdepth: 2

   user_guide/gui_walkthrough
   user_guide/setup_microscope
   user_guide/acquiring_home
   user_guide/case_studies/case_studies_home

.. toctree::
   :caption: Development
   :maxdepth: 2

   contributing/contributing_guidelines
   contributing/feature_container
   plugin/plugin_home
   api

**Outlook**
============
In the future, **navigate** will be accompanied by a hardware platform, **navigate-hardware**, which streamlines
the process of building advanced light-sheet microscopes through simplified optical, electronic, and mechanical
designs. **navigate-hardware** will be open-source and modular, allowing users to easily
customize their microscope to suit their needs. Supported variants will include
`Oblique Plane Microscopy <https://elifesciences.org/articles/57681>`_,
`Field Synthesis <https://www.nature.com/articles/s41592-019-0327-9>`_,
and `Axially Swept Light-Sheet Microscopy <https://www.nature.com/articles/s41596-022-00706-6>`_.

**Authors**
============
**Navigate** includes key contributions from numerous individuals, both past and present,
in `The Dean Lab <https://www.dean-lab.org>`_. These include Zach Marin, Annie Wang,
Dax Collison, Kevin Dean, Dushyant Mehra, Sampath Rapuri, Renil Gupta, Samir Mamtani,
Andrew Jamieson, Andrew York, Nathaniel Thayer, and more.

**Funding**
============
**navigate** is supported by the
`UT Southwestern and University of North Carolina Center for Cell Signaling
<https://cellularsignaltransduction.org>`_, a Biomedical Technology Development and Dissemination
Center funded by the NIH National Institute of General Medical Science (RM1GM145399).

**Index and search**
====================

* :ref:`genindex`
* :ref:`Search <search>`
