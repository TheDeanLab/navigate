# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Shared device reference-name definitions."""

DEVICE_REFERENCE_FIELDS = {
    "camera": ("serial_number",),
    "filter_wheel": ("type", "wheel_number"),
    "zoom": ("type", "servo_id"),
    "shutter": ("type", "channel"),
    "remote_focus": ("type", "channel"),
    "galvo": ("type", "channel"),
    "stage": ("type", "serial_number"),
    "laser": ("wavelength",),
    "mirror": ("type",),
}
