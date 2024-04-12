# Standard Imports

# Third Party Imports

# Local Imports
from navigate.model.devices.APIs.asi.asi_tiger_controller import (
    TigerController,
    TigerException,
)


class MFCTwoThousand(TigerController):
    """ASI MFC2000 Controller Class"""

    def set_speed_as_percent_max(self, pct):
        """Set speed as a percentage of the maximum speed

        Parameters
        ----------
        pct : float
            Percentage of the maximum speed
        """
        if self.default_axes_sequence is None:
            raise TigerException(
                "Unable to query system for axis sequence. Cannot set speed."
            )
        if self._max_speeds is None:
            # First, set the speed crazy high
            self.send_command(
                f"SPEED {' '.join([f'{ax}=1000' for ax in self.default_axes_sequence])}\r"  # noqa
            )
            self.read_response()

            # Next query the maximum speed
            self.send_command(
                f"SPEED {' '.join([f'{ax}?' for ax in self.default_axes_sequence])}\r"
            )
            res = self.read_response()
            new_max_speed = float(res.split()[0].split("=")[1])
            print(f"new_max_speed: {new_max_speed}")
            self._max_speeds = [new_max_speed * 1000]

        # Now set to pct
        self.send_command(
            f"SPEED {' '.join([f'{ax}={pct*speed:.7f}' for ax, speed in zip(self.default_axes_sequence, self._max_speeds)])}\r"  # noqa
        )
        self.read_response()
