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

from pathlib import Path

import pytest


def test_update_nested_dict():
    from aslm.log_files.log_functions import update_nested_dict

    test_dict = {"one": 2, "three": {4: {"metastasis": False}}}

    test_dict_updated = update_nested_dict(
        test_dict, lambda k, v: k == "metastasis", lambda x: True
    )

    assert test_dict_updated == {"one": 2, "three": {4: {"metastasis": True}}}


@pytest.mark.parametrize("logging_configuration", ["logging.yml"])
@pytest.mark.parametrize("logging_path", [None, Path("./")])
def test_log_setup(logging_configuration, logging_path):
    from datetime import datetime

    from aslm.log_files.log_functions import log_setup
    from aslm.config.config import get_aslm_path

    time = datetime.now()
    time_stamp = Path(
        "%s-%s-%s-%s%s"
        % (
            f"{time.year:04d}",
            f"{time.month:02d}",
            f"{time.day:02d}",
            f"{time.hour:02d}",
            f"{time.minute:02d}",
        )
    )

    if logging_path is None:
        logging_path = Path.joinpath(Path(get_aslm_path()), "logs")
    todays_path = Path.joinpath(logging_path, time_stamp)

    log_setup(logging_configuration, logging_path)

    assert Path.joinpath(todays_path, "performance.log").is_file()

    delete_folder(todays_path)


def delete_folder(top):
    # https://docs.python.org/3/library/os.html#os.walk
    # Delete everything reachable from the directory named in "top",
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if top == '/', it
    # could delete all your disk files.
    import os

    print(top)

    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

    os.rmdir(top)
