# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np

from navigate.controller.sub_controllers.camera_view import (
    BaseViewController,
    MIPViewController,
)


def test_try_to_display_image_defers_when_view_hidden():
    controller = BaseViewController.__new__(BaseViewController)
    controller._min_frame_interval = 0.0
    controller._last_enqueue_time = 0.0
    controller._pending_display_image = None
    controller._display_after_id = None
    controller._is_display_visible = lambda: False
    controller.view = SimpleNamespace(after_idle=MagicMock(return_value="cb-1"))

    image = np.array([[1, 2], [3, 4]], dtype=np.uint16)
    controller.try_to_display_image(image)

    assert controller._pending_display_image is image
    controller.view.after_idle.assert_not_called()


def test_request_display_if_needed_queues_when_visible():
    controller = BaseViewController.__new__(BaseViewController)
    controller._pending_display_image = np.array([[1]], dtype=np.uint16)
    controller._display_after_id = None
    controller._is_display_visible = lambda: True
    controller.view = SimpleNamespace(after_idle=MagicMock(return_value="cb-2"))

    controller._request_display_if_needed()

    controller.view.after_idle.assert_called_once_with(controller._flush_pending_display)
    assert controller._display_after_id == "cb-2"


def test_flush_pending_display_keeps_latest_when_hidden():
    controller = BaseViewController.__new__(BaseViewController)
    image = np.array([[9]], dtype=np.uint16)
    controller._pending_display_image = image
    controller._display_after_id = "cb-3"
    controller._is_display_visible = lambda: False
    controller.display_image = MagicMock()

    controller._flush_pending_display()

    assert controller._display_after_id is None
    assert controller._pending_display_image is image
    controller.display_image.assert_not_called()


def test_is_display_visible_true_for_popped_out_view():
    controller = BaseViewController.__new__(BaseViewController)
    controller.view = SimpleNamespace(is_docked=False, winfo_ismapped=lambda: True)

    assert controller._is_display_visible() is True


def test_mip_try_to_display_image_does_not_clear_when_hidden_and_disabled():
    controller = MIPViewController.__new__(MIPViewController)
    controller.image_mode = "z-stack"
    controller.display_enabled = SimpleNamespace(get=lambda: False)
    controller._is_display_visible = lambda: False
    controller._clear_mip = MagicMock()
    controller.identify_channel_index_and_slice = lambda: (0, 0)

    controller.try_to_display_image(np.array([[1]], dtype=np.uint16))

    controller._clear_mip.assert_not_called()
