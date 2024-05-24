========
REST-API
========

**navigate** has the ability to communicate with other image analysis software through REST-API interfaces.
In general, the REST-API is used to communicate with software that has different or conflicting
dependencies with the **navigate** codebase. Data is transferred via HTTP requests and responses,
which is faster and more efficient than locally saving the data and then loading it into another
piece of software, but slower than direct access of the data in memory.

An example of using our REST-API to communicate with ilastik, a widely used image segmentation tool,
is provided in our Case Studies section :doc:`here <case_studies/ilastik_segmentation>`.
The navigate ilastik Server plugin can be found `here <https://github
.com/TheDeanLab/navigate-ilastik-server>`_.
