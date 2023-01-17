"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
# """

import pytest


@pytest.fixture(scope="package")
def dummy_model():
    from aslm.model.dummy import DummyModel

    model = DummyModel()

    return model


# @pytest.fixture(scope="package")
# def dummy_model():
#     from types import SimpleNamespace

#     from aslm.model.model import Model
#     from multiprocessing import Manager, Queue
#     from aslm.config.config import get_configuration_paths, load_configs

#     event_queue = Queue(100)
#     manager = Manager()
#     (
#         configuration_path,
#         experiment_path,
#         etl_constants_path,
#         rest_api_path,
#     ) = get_configuration_paths()
#     configuration = load_configs(
#         manager,
#         configuration=configuration_path,
#         experiment=experiment_path,
#         etl_constants=etl_constants_path,
#         rest_api_config=rest_api_path,
#     )
#     model = Model(
#         USE_GPU=False,
#         args=SimpleNamespace(synthetic_hardware=True),
#         configuration=configuration,
#         event_queue=event_queue,
#     )

#     return model
