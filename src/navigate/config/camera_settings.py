"""Persistent camera defaults; experiment files retain their existing lifecycle."""

import os
from pathlib import Path
import tempfile

import yaml

from navigate.tools.common_functions import copy_proxy_object

ADVANCED_CAMERA_KEYS = (
    "bit_depth",
    "scan_speed",
    "defect_correction",
    "hot_pixel_correction",
    "trigger_source",
    "cooling",
    "output_triggers",
)


def seed_camera_defaults(configuration: dict) -> None:
    """Fill missing experiment selections without replacing explicit experiment intent.

    Nested selections are assigned as complete values so Manager proxies propagate
    changes between the GUI and model processes. Existing files need no migration.
    """
    parameters = configuration.get("experiment", {}).get("CameraParameters", {})
    for name, microscope in (
        configuration.get("configuration", {}).get("microscopes", {}).items()
    ):
        if name not in parameters:
            continue
        defaults = microscope.get("camera", {}).get("advanced_settings", {})
        for key in ADVANCED_CAMERA_KEYS:
            if key not in parameters[name] and key in defaults:
                parameters[name][key] = copy_proxy_object(defaults[key])


def camera_defaults(parameters: dict) -> dict:
    """Copy selected persistent fields, excluding runtime capabilities and telemetry."""
    return {
        key: copy_proxy_object(parameters[key])
        for key in ADVANCED_CAMERA_KEYS
        if key in parameters
    }


def save_camera_configuration(content_dict: dict, filename: str) -> None:
    """Atomically save configuration defaults with lossless YAML scalar quoting.

    Parameters
    ----------
    content_dict : dict
        The configuration portion of the shared dictionary, never the experiment.
    filename : str
        Existing application configuration path.
    """
    path = Path(filename)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            yaml.safe_dump(copy_proxy_object(content_dict), stream, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
