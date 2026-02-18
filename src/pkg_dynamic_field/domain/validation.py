from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, datetime
from typing import Any, List, Optional

from .entities import FieldDefinition, FieldSchema, FieldType
from .exceptions import FieldError


def validate_field_values(
    schema: FieldSchema,
    raw_values: dict[str, Any],
) -> List[FieldError]:
    errors: List[FieldError] = []

    for defn in schema.top_level_definitions:
        value = raw_values.get(defn.key)
        errors.extend(validate_single_field(defn, value, defn.key))

    return errors


def validate_single_field(
    defn: FieldDefinition,
    value: Any,
    path: str,
) -> List[FieldError]:
    if defn.repeatable:
        return _validate_repeatable(defn, value, path)
    if defn.translatable:
        return _validate_translatable(defn, value, path)
    if defn.type == FieldType.COMPOSITE:
        return _validate_composite(defn, value, path)
    return _validate_scalar(defn, value, path)


def _validate_repeatable(
    defn: FieldDefinition,
    value: Any,
    path: str,
) -> List[FieldError]:
    errors: List[FieldError] = []
    required = defn.constraints.get("required", False)

    if value is None:
        if required:
            errors.append(FieldError(path=path, message="This field is required.", code="required"))
        return errors

    if not isinstance(value, list):
        errors.append(FieldError(path=path, message="Expected a list.", code="type"))
        return errors

    min_items = defn.constraints.get("min_items")
    max_items = defn.constraints.get("max_items")
    if min_items is not None and len(value) < min_items:
        errors.append(FieldError(path=path, message=f"Must have at least {min_items} items.", code="min_items"))
    if max_items is not None and len(value) > max_items:
        errors.append(FieldError(path=path, message=f"Must have at most {max_items} items.", code="max_items"))

    non_repeatable = replace(defn, repeatable=False)
    for i, item in enumerate(value):
        item_path = f"{path}[{i}]"
        if defn.translatable:
            errors.extend(_validate_translatable(non_repeatable, item, item_path))
        elif defn.type == FieldType.COMPOSITE:
            errors.extend(_validate_composite(non_repeatable, item, item_path))
        else:
            errors.extend(_validate_scalar(non_repeatable, item, item_path))

    return errors


def _validate_translatable(
    defn: FieldDefinition,
    value: Any,
    path: str,
) -> List[FieldError]:
    errors: List[FieldError] = []
    required = defn.constraints.get("required", False)

    if value is None:
        if required:
            errors.append(FieldError(path=path, message="This field is required.", code="required"))
        return errors

    if not isinstance(value, dict):
        errors.append(FieldError(path=path, message="Expected a translatable object with 'default' key.", code="type"))
        return errors

    if "default" not in value:
        errors.append(FieldError(path=f"{path}.default", message="Default value is required.", code="required"))
    else:
        non_translatable = replace(defn, translatable=False)
        errors.extend(_validate_scalar_or_composite(non_translatable, value["default"], f"{path}.default"))

    translations = value.get("translations", {})
    if isinstance(translations, dict):
        non_translatable = replace(defn, translatable=False)
        for lang, lang_value in translations.items():
            errors.extend(_validate_scalar_or_composite(non_translatable, lang_value, f"{path}.translations.{lang}"))

    return errors


def _validate_scalar_or_composite(
    defn: FieldDefinition,
    value: Any,
    path: str,
) -> List[FieldError]:
    if defn.type == FieldType.COMPOSITE:
        return _validate_composite(defn, value, path)
    return _validate_scalar(defn, value, path)


def _validate_composite(
    defn: FieldDefinition,
    value: Any,
    path: str,
) -> List[FieldError]:
    errors: List[FieldError] = []
    required = defn.constraints.get("required", False)

    if value is None:
        if required:
            errors.append(FieldError(path=path, message="This field is required.", code="required"))
        return errors

    if not isinstance(value, dict):
        errors.append(FieldError(path=path, message="Expected an object.", code="type"))
        return errors

    for child in defn.children:
        child_value = value.get(child.key)
        child_path = f"{path}.{child.key}"
        errors.extend(validate_single_field(child, child_value, child_path))

    return errors


def _validate_scalar(
    defn: FieldDefinition,
    value: Any,
    path: str,
) -> List[FieldError]:
    errors: List[FieldError] = []
    required = defn.constraints.get("required", False)

    if value is None:
        if required:
            errors.append(FieldError(path=path, message="This field is required.", code="required"))
        return errors

    # Type check
    type_error = _check_type(defn.type, value, path)
    if type_error:
        errors.append(type_error)
        return errors

    # Constraints
    constraints = defn.constraints

    if defn.type in (FieldType.INT, FieldType.FLOAT):
        min_val = constraints.get("min")
        max_val = constraints.get("max")
        if min_val is not None and value < min_val:
            errors.append(FieldError(path=path, message=f"Value must be >= {min_val}.", code="min"))
        if max_val is not None and value > max_val:
            errors.append(FieldError(path=path, message=f"Value must be <= {max_val}.", code="max"))

    if defn.type == FieldType.STRING:
        min_length = constraints.get("min_length")
        max_length = constraints.get("max_length")
        pattern = constraints.get("pattern")
        if min_length is not None and len(value) < min_length:
            errors.append(FieldError(path=path, message=f"Must be at least {min_length} characters.", code="min_length"))
        if max_length is not None and len(value) > max_length:
            errors.append(FieldError(path=path, message=f"Must be at most {max_length} characters.", code="max_length"))
        if pattern is not None and not re.search(pattern, value):
            errors.append(FieldError(path=path, message=f"Must match pattern: {pattern}", code="pattern"))

    allowed_values = constraints.get("allowed_values")
    if allowed_values is not None and value not in allowed_values:
        errors.append(FieldError(path=path, message=f"Value must be one of: {allowed_values}", code="allowed_values"))

    return errors


def _check_type(field_type: FieldType, value: Any, path: str) -> Optional[FieldError]:
    type_map = {
        FieldType.STRING: str,
        FieldType.INT: int,
        FieldType.FLOAT: (int, float),
        FieldType.BOOL: bool,
    }

    if field_type in type_map:
        expected = type_map[field_type]
        # bool is subclass of int in Python, so check bool first
        if field_type == FieldType.INT and isinstance(value, bool):
            return FieldError(path=path, message=f"Expected type '{field_type.value}'.", code="type")
        if not isinstance(value, expected):
            return FieldError(path=path, message=f"Expected type '{field_type.value}'.", code="type")

    if field_type in (FieldType.DATE, FieldType.DATETIME):
        if not isinstance(value, str):
            return FieldError(path=path, message=f"Expected ISO format string for '{field_type.value}'.", code="type")
        try:
            if field_type == FieldType.DATE:
                date.fromisoformat(value)
            else:
                datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return FieldError(path=path, message=f"Invalid {field_type.value} format.", code="type")

    return None
