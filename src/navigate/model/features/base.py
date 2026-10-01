# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Base types for executable feature-list nodes."""

# Standard library imports
import inspect


class FeatureBase:
    """Marker base class for real feature-list nodes.

    Classes shown in feature editors should inherit from this class directly or
    indirectly. Helper classes imported into feature modules can remain plain
    classes and will not be treated as feature nodes.
    """


def is_feature_class(candidate) -> bool:
    """Return whether ``candidate`` is an executable feature class."""
    return (
        inspect.isclass(candidate)
        and issubclass(candidate, FeatureBase)
        and candidate is not FeatureBase
    )
