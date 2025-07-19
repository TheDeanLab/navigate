# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.
from sphinx.cmd.quickstart import suffix


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


class StageLimitsController:
    """Controller for the Stage Limits popup."""

    def __init__(self, popup, parent_controller, *args, **kwargs):
        """Initialize the StageLimitsController class.

        Parameters
        ----------
        root : tk.Tk
            The root window
        popup : PopUp
            The popup window for stage limits
        parent_controller : Controller
            The parent controller that manages this popup
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """

        #: list: List of stages available in the system.
        self.num_stages = parent_controller.configuration_controller.all_stage_axes

        #: dict: List of minimum limits for each stage.
        self.min_limits = (
            parent_controller.configuration_controller.get_stage_limits_min_limits(
                suffix="_min"
            )
        )

        #: dict: List of maximum limits for each stage.
        self.max_limits = (
            parent_controller.configuration_controller.get_stage_limits_max_limits(
                suffix="_max"
            )
        )

        #: PopUp: Popup window for the stage limits.
        self.view = popup

        self.view.populate_view(self.num_stages)
