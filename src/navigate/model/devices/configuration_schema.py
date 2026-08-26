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

# Standard Library Imports
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple


@dataclass(frozen=True)
class SettingSpec:
    """Description of one user-editable setting or feature parameter.

    ``choices`` defines a closed set of values. ``dynamic_source`` identifies
    choices that should be resolved at render time, and ``depends_on`` names the
    parameter that provides context for dependent choices. ``minimum``,
    ``maximum``, and ``step`` define a numeric range; they are intentionally
    mutually exclusive with ``choices``.
    """

    value_type: type
    default: Any = None
    label: Optional[str] = None
    help_text: Optional[str] = None
    choices: Optional[Tuple[Any, ...]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    required: bool = False
    dynamic_source: Optional[str] = None
    depends_on: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate a schema definition when its class is imported."""
        has_range = any(
            value is not None for value in (self.minimum, self.maximum, self.step)
        )
        if self.choices is not None and has_range:
            raise ValueError(
                "SettingSpec choices and numeric ranges are mutually exclusive."
            )
        if has_range and self.value_type not in (int, float):
            raise ValueError("Numeric ranges require an int or float SettingSpec.")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("SettingSpec minimum cannot exceed maximum.")
        if self.step is not None and self.step <= 0:
            raise ValueError("SettingSpec step must be greater than zero.")

    @property
    def display_label(self) -> str:
        """Return the configured label, falling back to the setting key at render time."""
        return self.label or ""


@dataclass(frozen=True)
class CollectionSpec:
    """Description of a repeatable group of persisted configuration values.

    ``storage='mapping'`` stores rows as a YAML mapping, using ``key_field`` as
    the mapping key and ``value_field`` as its value. ``storage='parallel_mappings'``
    stores selected row fields as separate YAML mappings keyed by ``key_field``.
    ``storage='nested_mapping'`` stores calibration rows as
    ``solvent -> axis -> zoom -> position``.
    """

    item_schema: Mapping[str, SettingSpec]
    storage: str = "mapping"
    key_field: str = "name"
    value_field: str = "value"
    storage_fields: Optional[Tuple[str, ...]] = None
    label: Optional[str] = None
    help_text: Optional[str] = None
    minimum_items: int = 0

    def __post_init__(self) -> None:
        """Validate collection metadata at class-definition time."""
        if self.storage not in {"mapping", "parallel_mappings", "nested_mapping"}:
            raise ValueError("CollectionSpec has an unsupported storage type.")
        if self.key_field not in self.item_schema:
            raise ValueError("CollectionSpec key_field must be in item_schema.")
        if self.value_field not in self.item_schema:
            raise ValueError("CollectionSpec value_field must be in item_schema.")
        if self.storage == "parallel_mappings":
            if not self.storage_fields or any(
                field not in self.item_schema for field in self.storage_fields
            ):
                raise ValueError(
                    "Parallel mapping collections require valid storage fields."
                )
        if self.storage == "nested_mapping" and set(self.item_schema) != {
            "solvent",
            "axis",
            "zoom",
            "position",
        }:
            raise ValueError(
                "Nested mapping collections require solvent, axis, zoom, and position fields."
            )
        if self.minimum_items < 0:
            raise ValueError("CollectionSpec minimum_items cannot be negative.")


def merge_configuration_schemas(
    *schemas: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge schemas in inheritance order, allowing later schemas to override.

    The caller supplies parent schemas first and child schemas last.
    """
    merged: dict[str, Any] = {}
    for schema in schemas:
        merged.update(schema)
    return merged
