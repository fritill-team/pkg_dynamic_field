"""pkg_dynamic_field — Entity-agnostic dynamic field definitions, validation, and value storage."""
from __future__ import annotations

# Domain
from .domain.entities import FieldType, FieldDefinition, FieldSchema, FieldValue
from .domain.events import DomainEvent, FieldSchemaCreated, FieldSchemaUpdated, FieldValuesSet
from .domain.exceptions import FieldError, FieldSchemaNotFoundError, FieldValidationError
from .domain.validation import validate_field_values

# Application
from .application.ports import EventBus, FieldSchemaRepo, FieldValueRepo, DynamicFieldUoW
from .application.dtos import FieldDefinitionCmd, UpsertFieldSchemaCmd
from .application.use_cases import UpsertFieldSchema, GetFieldSchema, SetFieldValues, GetFieldValues

__all__ = [
    # Domain entities
    "FieldType",
    "FieldDefinition",
    "FieldSchema",
    "FieldValue",
    # Domain events
    "DomainEvent",
    "FieldSchemaCreated",
    "FieldSchemaUpdated",
    "FieldValuesSet",
    # Domain exceptions
    "FieldError",
    "FieldSchemaNotFoundError",
    "FieldValidationError",
    # Domain validation
    "validate_field_values",
    # Application ports
    "EventBus",
    "FieldSchemaRepo",
    "FieldValueRepo",
    "DynamicFieldUoW",
    # Application DTOs
    "FieldDefinitionCmd",
    "UpsertFieldSchemaCmd",
    # Application use cases
    "UpsertFieldSchema",
    "GetFieldSchema",
    "SetFieldValues",
    "GetFieldValues",
]
