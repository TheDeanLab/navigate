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
import ast
import importlib
import logging
from pathlib import Path
from typing import Optional

# Local Imports
from navigate.config.configuration_schema import (
    CollectionSpec,
    SettingSpec,
    merge_configuration_schemas,
)
from navigate.model.devices.device_types import SerialDevice, SequenceDevice
from navigate.tools.common_functions import load_param_from_module

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def device_directory() -> Path:
    """Return the package directory containing device implementations."""
    return Path(__file__).resolve().parents[1] / "model" / "devices"


def category_base_class_name(category: str) -> str:
    """Return a category's base class name, including acronym exceptions."""
    base_names = {"daq": "DAQBase"}
    return base_names.get(
        category,
        "".join(word.title() for word in category.split("_")) + "Base",
    )


def category_model_suffix(category: str) -> str:
    """Return the class-name suffix for a device category."""
    return category_base_class_name(category).removesuffix("Base")


def strip_category_model_suffix(category: str, model: str) -> str:
    """Strip a category class suffix from a model name if present."""
    suffix = category_model_suffix(category)
    if model.casefold().endswith(suffix.casefold()):
        return model[: -len(suffix)]
    return model


def canonical_device_type(category: str, device_type: object) -> Optional[str]:
    """Normalize a device type token to ``manufacturer.model``.

    Supported inputs include ``manufacturer.model``,
    ``manufacturer.model<DeviceCategory>``, ``model<DeviceCategory>``, and
    ``model``.
    """
    if not isinstance(device_type, str) or not device_type.strip():
        return None
    raw_type = device_type.strip()

    if "." in raw_type:
        manufacturer, model = raw_type.split(".")[:2]
        model = _legacy_device_model(model)
        return ".".join(
            (
                _canonical_manufacturer(category, manufacturer),
                strip_category_model_suffix(category, model),
            )
        )

    raw_type = _legacy_device_model(raw_type)
    model = strip_category_model_suffix(category, raw_type)
    database_match = _canonical_device_type_from_database(category, raw_type, model)
    if database_match is not None:
        return database_match

    class_match = _canonical_device_type_from_classes(category, model)
    if class_match is not None:
        return class_match

    return None


def _canonical_manufacturer(category: str, manufacturer: str) -> str:
    """Return the package manufacturer name for a possibly cased token."""
    manufacturer_casefold = manufacturer.casefold()
    category_path = device_directory() / category
    if category_path.exists():
        for path in category_path.glob("*.py"):
            if path.stem.casefold() == manufacturer_casefold:
                return path.stem
    return manufacturer.casefold()


def _legacy_device_model(model: str) -> str:
    """Return the current model name for a deceased model token."""
    try:
        legacy_names = load_param_from_module(
            "navigate.config.configuration_database", "deceased_device_type_names"
        )
    except (ImportError, AttributeError, ModuleNotFoundError):
        return model
    return {
        str(old_name).casefold(): str(new_name)
        for old_name, new_name in legacy_names.items()
    }.get(model.casefold(), model)


def _canonical_device_type_from_database(
    category: str, raw_type: str, model: str
) -> Optional[str]:
    """Resolve a type through configuration_database mappings."""
    try:
        device_types = load_param_from_module(
            "navigate.config.configuration_database", category + "_device_types"
        )
    except (ImportError, AttributeError, ModuleNotFoundError):
        return None

    suffix = category_model_suffix(category)
    raw_type_casefold = raw_type.casefold()
    model_casefold = model.casefold()
    for display_name, value in device_types.items():
        if isinstance(value, tuple):
            database_model, manufacturer = value
        else:
            database_model = value
            manufacturer = str(value).casefold()

        database_model = str(database_model)
        candidates = {
            str(display_name),
            database_model,
            f"{database_model}{suffix}",
        }
        if (
            raw_type_casefold in {candidate.casefold() for candidate in candidates}
            or model_casefold == database_model.casefold()
        ):
            manufacturer = _canonical_manufacturer(category, str(manufacturer))
            return f"{manufacturer}.{database_model}"
    return None


def _canonical_device_type_from_classes(category: str, model: str) -> Optional[str]:
    """Resolve a type by scanning device classes when no database entry exists."""
    class_name = model + category_model_suffix(category)
    category_path = device_directory() / category
    if not category_path.exists():
        return None
    for path in sorted(category_path.glob("*.py")):
        if path.stem in {"__init__", "base"}:
            continue
        try:
            classes = module_classes(category, path.stem)
        except (FileNotFoundError, SyntaxError):
            continue
        if class_name.casefold() in {name.casefold() for name in classes}:
            return f"{path.stem}.{model}"
    return None


def module_classes(category: str, manufacturer: str) -> dict[str, list[str]]:
    """Return class names mapped to directly declared base-class names."""
    module = ast.parse(
        (device_directory() / category / (manufacturer + ".py")).read_text(
            encoding="utf-8"
        )
    )
    return {
        node.name: [
            (
                base.id
                if isinstance(base, ast.Name)
                else base.attr if isinstance(base, ast.Attribute) else ""
            )
            for base in node.bases
        ]
        for node in module.body
        if isinstance(node, ast.ClassDef)
    }


def class_inherits(
    category: str, manufacturer: str, class_name: str, parent: str
) -> bool:
    """Check inheritance without importing device hardware APIs."""

    def module_details(
        module_name: str,
    ) -> tuple[dict[str, list[str]], dict[str, str]]:
        module = ast.parse(
            (device_directory() / category / (module_name + ".py")).read_text(
                encoding="utf-8"
            )
        )
        classes = {
            node.name: [
                (
                    base.id
                    if isinstance(base, ast.Name)
                    else base.attr if isinstance(base, ast.Attribute) else ""
                )
                for base in node.bases
            ]
            for node in module.body
            if isinstance(node, ast.ClassDef)
        }
        imports = {}
        module_prefix = f"navigate.model.devices.{category}."
        for node in module.body:
            if not (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(module_prefix)
            ):
                continue
            imported_module = node.module.removeprefix(module_prefix)
            if "." in imported_module:
                continue
            for alias in node.names:
                imports[alias.asname or alias.name] = imported_module
        return classes, imports

    def inherits(module_name: str, name: str, visited: set[tuple[str, str]]) -> bool:
        key = (module_name, name)
        if key in visited:
            return False
        visited.add(key)
        try:
            classes, imports = module_details(module_name)
        except FileNotFoundError:
            return False
        if name not in classes:
            return False
        for base in classes[name]:
            if base == parent:
                return True
            if inherits(module_name, base, visited):
                return True
            imported_module = imports.get(base)
            if imported_module and inherits(imported_module, base, visited):
                return True
        return False

    return inherits(manufacturer, class_name, set())


def get_connect_params(category: str, manufacturer: str, class_name: str) -> list[str]:
    """Read literal ``get_connect_params`` values from a class or local ancestor."""
    module = ast.parse(
        (device_directory() / category / (manufacturer + ".py")).read_text(
            encoding="utf-8"
        )
    )
    nodes = {node.name: node for node in module.body if isinstance(node, ast.ClassDef)}

    def inspect(name: str, visited: set[str]) -> list[str]:
        if name in visited or name not in nodes:
            return []
        visited.add(name)
        node = nodes[name]
        for function in node.body:
            if (
                isinstance(function, ast.FunctionDef)
                and function.name == "get_connect_params"
            ):
                for statement in function.body:
                    if isinstance(statement, ast.Return) and isinstance(
                        statement.value, (ast.List, ast.Tuple)
                    ):
                        return [
                            value.value
                            for value in statement.value.elts
                            if isinstance(value, ast.Constant)
                            and isinstance(value.value, str)
                        ]
        for base in node.bases:
            base_name = (
                base.id
                if isinstance(base, ast.Name)
                else base.attr if isinstance(base, ast.Attribute) else ""
            )
            params = inspect(base_name, visited)
            if params:
                return params
        return []

    return inspect(class_name, set())


def get_class_configuration_schema(
    category: str, manufacturer: str, class_name: str
) -> dict[str, SettingSpec]:
    """Read class-level schemas without importing device hardware APIs."""
    module = ast.parse(
        (device_directory() / category / (manufacturer + ".py")).read_text(
            encoding="utf-8"
        )
    )
    nodes = {node.name: node for node in module.body if isinstance(node, ast.ClassDef)}

    def setting_spec(call: ast.Call) -> Optional[SettingSpec]:
        if not (
            isinstance(call.func, ast.Name)
            and call.func.id == "SettingSpec"
            and call.args
            and isinstance(call.args[0], ast.Name)
        ):
            return None
        value_type = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
        }.get(call.args[0].id)
        if value_type is None:
            return None
        kwargs = {}
        for keyword in call.keywords:
            if keyword.arg is None:
                continue
            try:
                kwargs[keyword.arg] = ast.literal_eval(keyword.value)
            except ValueError:
                continue
        return SettingSpec(value_type, **kwargs)

    def collection_spec(call: ast.Call) -> Optional[CollectionSpec]:
        if not (isinstance(call.func, ast.Name) and call.func.id == "CollectionSpec"):
            return None
        keywords = {
            keyword.arg: keyword.value for keyword in call.keywords if keyword.arg
        }
        item_schema_node = keywords.pop("item_schema", None)
        if not isinstance(item_schema_node, ast.Dict):
            return None
        item_schema = {}
        for key, value in zip(item_schema_node.keys, item_schema_node.values):
            if not (
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and isinstance(value, ast.Call)
            ):
                continue
            spec = setting_spec(value)
            if spec is not None:
                item_schema[key.value] = spec
        if not item_schema:
            return None
        kwargs = {"item_schema": item_schema}
        for name, value in keywords.items():
            try:
                kwargs[name] = ast.literal_eval(value)
            except ValueError:
                continue
        try:
            return CollectionSpec(**kwargs)
        except (TypeError, ValueError):
            return None

    def class_schema(node: ast.ClassDef) -> dict[str, object]:
        for statement in node.body:
            if not (
                isinstance(statement, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "configuration_schema"
                    for target in statement.targets
                )
                and isinstance(statement.value, ast.Dict)
            ):
                continue
            schema: dict[str, object] = {}
            for key, value in zip(statement.value.keys, statement.value.values):
                if not (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(value, ast.Call)
                ):
                    continue
                spec = setting_spec(value) or collection_spec(value)
                if spec is not None:
                    schema[key.value] = spec
            return schema
        return {}

    def inherited_schema(name: str, visited: set[str]) -> dict[str, object]:
        if name in visited or name not in nodes:
            return {}
        visited.add(name)
        node = nodes[name]
        schemas = []
        for base in node.bases:
            base_name = (
                base.id
                if isinstance(base, ast.Name)
                else base.attr if isinstance(base, ast.Attribute) else ""
            )
            schemas.append(inherited_schema(base_name, visited))
        schemas.append(class_schema(node))
        return merge_configuration_schemas(*schemas)

    return inherited_schema(class_name, set())


def get_configuration_schema(
    category: str, manufacturer: str, model: str
) -> dict[str, object]:
    """Resolve the currently available configuration schema for a device."""
    connection_schema = {
        property_name: SettingSpec(
            str,
            default="",
            label=property_name.replace("_", " ").title(),
            help_text="Connection value required to initialize this device.",
            required=True,
        )
        for property_name in get_connect_params(category, manufacturer, model)
    }
    schemas = [connection_schema]
    if class_inherits(category, manufacturer, model, "SerialDevice"):
        schemas.append(SerialDevice.configuration_schema)
    if class_inherits(category, manufacturer, model, "SequenceDevice"):
        schemas.append(SequenceDevice.configuration_schema)
    base_class_name = category_base_class_name(category)
    if class_inherits(category, manufacturer, model, base_class_name):
        try:
            base_module = importlib.import_module(
                f"navigate.model.devices.{category}.base"
            )
            base_class = getattr(base_module, base_class_name)
            schemas.append(getattr(base_class, "configuration_schema", {}))
        except (ImportError, AttributeError):
            logger.exception(
                "Could not load the configuration schema for %s.", base_class_name
            )
    schemas.append(get_class_configuration_schema(category, manufacturer, model))
    return merge_configuration_schemas(*schemas)
