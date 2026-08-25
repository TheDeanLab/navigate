# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Feature-list editor helpers for schema-backed parameter values."""

# Standard library imports
import ast

# Local application imports
from navigate.model.devices.configuration_schema import SettingSpec


def coerce_feature_parameter(
    parameter_name: str,
    value: object,
    spec: SettingSpec,
) -> object:
    """Convert an editor value to the type declared by ``spec``.

    Raises
    ------
    ValueError
        If the value is missing, cannot be converted, or violates schema bounds.
    """
    if spec.value_type is bool:
        if isinstance(value, bool):
            coerced = value
        else:
            normalized = str(value).strip()
            if normalized == "":
                if spec.required:
                    raise ValueError(f"{parameter_name} is required.")
                return None
            if normalized not in {"True", "False"}:
                raise ValueError(f"{parameter_name} must be True or False.")
            coerced = normalized == "True"
    else:
        normalized = str(value).strip()
        if normalized == "":
            if spec.required:
                raise ValueError(f"{parameter_name} is required.")
            return None
        if normalized == "None" and not spec.required:
            return None

        try:
            if spec.value_type is int:
                coerced = int(normalized)
            elif spec.value_type is float:
                coerced = float(normalized)
            elif spec.value_type is dict:
                coerced = ast.literal_eval(normalized)
                if not isinstance(coerced, dict):
                    raise ValueError
            elif spec.value_type is list:
                coerced = ast.literal_eval(normalized)
                if not isinstance(coerced, list):
                    raise ValueError
            elif spec.value_type is tuple:
                coerced = ast.literal_eval(normalized)
                if not isinstance(coerced, tuple):
                    raise ValueError
            else:
                coerced = normalized
        except (TypeError, ValueError, SyntaxError):
            type_name = getattr(spec.value_type, "__name__", str(spec.value_type))
            raise ValueError(f"{parameter_name} must be a valid {type_name}.") from None

    if spec.choices is not None and coerced not in spec.choices:
        raise ValueError(f"{parameter_name} must be one of {spec.choices}.")
    if spec.minimum is not None and coerced < spec.minimum:
        raise ValueError(f"{parameter_name} must be at least {spec.minimum}.")
    if spec.maximum is not None and coerced > spec.maximum:
        raise ValueError(f"{parameter_name} must be no more than {spec.maximum}.")
    return coerced


def infer_feature_parameter_spec(value: object) -> SettingSpec:
    """Build a backward-compatible schema from an existing default value."""
    if isinstance(value, bool):
        return SettingSpec(bool, default=value)
    if isinstance(value, int) and not isinstance(value, bool):
        return SettingSpec(int, default=value)
    if isinstance(value, float):
        return SettingSpec(float, default=value)
    if isinstance(value, dict):
        return SettingSpec(dict, default=value)
    if isinstance(value, list):
        return SettingSpec(list, default=value)
    if isinstance(value, tuple):
        return SettingSpec(tuple, default=value)
    return SettingSpec(str, default=value)
