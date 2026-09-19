# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Private lifecycle state for model-owned resolution changes."""

from dataclasses import dataclass, field
import threading
from typing import Any, Dict, List, Optional


@dataclass
class _ResolutionChangeTask:
    """Track one resolution change or recovery movement inside the model."""

    task_id: int
    resolution_value: str
    former_microscope_name: str
    target_microscope_name: str
    cancel_event: threading.Event = field(default_factory=threading.Event)
    state: str = "changing"
    worker: Optional[threading.Thread] = None
    previous_position: Optional[Dict[str, Any]] = None
    stopped_position: Optional[Dict[str, Any]] = None
    stop_errors: List[str] = field(default_factory=list)
