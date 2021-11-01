<hr>

# v1.2.0
**User Facing**
* Added ability to pull and push private images

**Background**
* Changed login method from using GitHub Actions to using Python
* Added cleanup step after each image test in CI to ensure that CI VM does not run out of disk space

<hr>

# v1.1.2
**User Facing**
* Added template-relations.yaml for better setup instructions
* Fixed skipping over image testing after build
* Fixed print of relationships.yaml to not print multiple hierchies, flattenting file representation

**Background**
* Fixed issue where it would be pushing nested arrays to parent and child images.
* Cleaned up testing paths and the tests directory.

<hr>

# v1.1.1
**User Facing**
* Fixed CI to expect list of changed files instead of string of a single file

<hr>

# v1.1.0
**User Facing**
* Split testing categories into tests for images and tests for auto-docker
* Fixed recursion bug when adding image

<hr>

# v1.0.0
**User Facing**
* Migrated from bash to python for building and testing
* Added in wiki for updated instructions
* Added unit test for auto-docker functionality


<hr>

# v0.1.0
**INITIAL BETA VERSION**\
Intial beta release of auto-docker code.
This is the prototype version written in bash and using github actions.
<hr>
