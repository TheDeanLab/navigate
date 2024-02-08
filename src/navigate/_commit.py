# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


# Standard Library Imports
import os
import subprocess

# Third Party Imports

# Local Imports


def get_git_revision_hash() -> str:
    """ Get the git commit hash of the current repository.

    This function will return the git commit hash of the current repository, or None if
    the current directory is not a git repository.

    Returns:
    --------
    commit_hash : str
        The git commit hash of the current repository, or None if the current directory
        is not a git repository
    """
    working_directory = os.getcwd()
    file_directory = os.path.abspath(os.path.dirname(__file__))
    os.chdir(file_directory)

    try:
        is_git_repo = subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stderr=subprocess.DEVNULL).decode("ascii").strip()
        if is_git_repo:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"]).decode("ascii").strip()
        else:
            commit_hash = None
    except subprocess.CalledProcessError:
        commit_hash = None

    os.chdir(working_directory)
    return commit_hash

def get_version_from_file(file_name='VERSION'):
    """ Retrieve the version from a file in the same directory as this file.

    The VERSION file located in src/navigate/VERSION contains the version of the
    package when deployed to PyPI.

    Parameters
    ----------
    file_name : str
        The name of the file to read the version from. Default is 'VERSION'

    Returns
    -------
    version : str
        The version of the package
    """
    absolute_path = os.path.abspath(__file__)
    file_path = os.path.join(os.path.dirname(absolute_path), file_name)

    try:
        with open(file_path, 'r') as file:
            version = file.read().strip()
        return version
    except FileNotFoundError:
        return "unknown"

__commit__ = get_git_revision_hash()
if __commit__ is None:
    __commit__ = get_version_from_file()

print(f"Commit: {__commit__}")