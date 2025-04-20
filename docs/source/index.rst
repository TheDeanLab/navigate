
.. _navigate-home:

############
**navigate**
############


**navigate** is an open-source Python software for light-sheet microscope control. It focuses on smart microscopy applications by providing reusable acquisition and analysis routines, termed :ref:`features <features>`, that can be chained in arbitrary orders to create custom acquisition protocols. **navigate** is designed to accommodate the needs of a diverse user base, from biologists with no programming experience to advanced technology developers.

**Project Philosophy**
=========================

* Prioritize standard library imports for maximum stability, and minimize external dependencies.
* Abstraction layer to drive different camera types, etc.
* Plugin architecture for extensibility.
* Maximize productivity for biological users through robust graphical user interface-based workflows.
* Performant and responsive.
* Brutally obvious, well-documented, clean code organized in an industry standard Model-View-Controller architecture.

.. note::

   This project is under active development. See our `GitHub repository for updates <https://github.com/TheDeanLab/navigate>`_.

.. warning::

    Please be advised that while the Dean Lab has implemented several safeguards in the automation of hardware, including but not limited to stage limits, voltage minimums, and maximums, are more, there are inherent risks associated with the use of such automated systems. Despite these precautions, the complexity and nature of automated hardware can lead to unpredictable outcomes. Therefore, the Dean Lab and UT Southwestern expressly disclaim any responsibility for any damages, losses, or injuries that may arise from or be related to the use of **navigate**. Users should be aware of these risks and agree to utilize **navigate** at their own risk.


.. toctree::
   :caption: Getting Started
   :maxdepth: 1

   01_getting_started/01_quick_start/01_quick_start
   01_getting_started/02_software_installation/02_software_installation
   01_getting_started/03_i_want_to/03_i_want_to


.. toctree::
   :caption: User Guide
   :maxdepth: 1

   02_user_guide/01_supported_hardware/hardware_home
   02_user_guide/02_file_formats/file_formats
   02_user_guide/03_user_interface_walkthrough/user_interface_walkthrough
   02_user_guide/04_microscope_setup/setup_microscope
   02_user_guide/05_acquiring_data/acquiring_home
   02_user_guide/06_case_studies/case_studies_home

.. toctree::
   :caption: Development
   :maxdepth: 1

   03_contributing/01_contributing_guidelines/01_contributing_guidelines
   03_contributing/02_developer_install/02_developer_install
   03_contributing/03_software_architecture/software_architecture
   03_contributing/04_feature_container/feature_container
   03_contributing/05_restapi/restapi
   03_contributing/06_plugin/plugin_home

.. toctree::
   :caption: Troubleshooting & Known Issues
   :maxdepth: 1

   04_faq/troubleshooting/troubleshooting_home
   04_faq/issues/issues_home

.. toctree::
   :caption: Plugins
   :maxdepth: 1

   navigate Plugin Template <https://github.com/TheDeanLab/navigate-plugin-template>
   navigate Confocal Projection <https://github.com/TheDeanLab/navigate-confocal-projection>
   navigate at Scale <https://github.com/TheDeanLab/navigate-at-scale>
   navigate Constant Velocity Acquisition <https://github.com/TheDeanLab/navigate-constant-velocity-acquisition>
   navigate MMCore <https://github.com/TheDeanLab/navigate-mmcore-plugin>
   navigate ilastik Server <https://github.com/TheDeanLab/navigate-ilastik-server>
   navigate Photoactivation <https://github.com/TheDeanLab/navigate-photoactivation>

.. toctree::
   :caption: Reference
   :maxdepth: 1

   05_reference/implementations/implementations
   05_reference/api


**Authors**
============
**navigate** includes key contributions from numerous individuals, both past and present, in `The Dean Lab <https://www.dean-lab.org>`_. Please see the accompanying manuscript for a full list of contributors. :ref:`Outside contributors  <contributing_guidelines>` are welcome.

**Funding**
============
**navigate** is supported by the

- NIH National Institute of General Medical Science (RM1GM145399).
- NIH National Cancer Institute (1U54CA268072).
- `Simmons Comprehensive Cancer Center <https://www.utsouthwestern.edu/departments/simmons/>`_ Translational Seed Grant.
- `UTSW President's Research Council <https://engage.utsouthwestern.edu/pages/membership-giving/membership-giving---presidents-research-council>`_
