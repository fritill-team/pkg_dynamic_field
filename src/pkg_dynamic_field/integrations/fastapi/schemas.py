from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ...domain.entities import FieldType


class FieldDefinitionInput(BaseModel):
    key: str
    type: FieldType
    constraints: Dict[str, Any] = Field(default_factory=dict)
    ui_config: Dict[str, Any] = Field(default_factory=dict)
    translatable: bool = False
    repeatable: bool = False
    sort_order: int = 0
    group: Optional[str] = None
    children: List[FieldDefinitionInput] = Field(default_factory=list)


# Recursive model needs rebuild
FieldDefinitionInput.model_rebuild()


class UpsertFieldSchemaRequest(BaseModel):
    definitions: List[FieldDefinitionInput]


class FieldDefinitionResponse(BaseModel):
    id: UUID
    key: str
    type: FieldType
    parent_id: Optional[UUID] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    ui_config: Dict[str, Any] = Field(default_factory=dict)
    translatable: bool = False
    repeatable: bool = False
    sort_order: int = 0
    group: Optional[str] = None
    children: List[FieldDefinitionResponse] = Field(default_factory=list)


FieldDefinitionResponse.model_rebuild()


class FieldSchemaResponse(BaseModel):
    id: UUID
    kind: str
    version: int
    definitions: List[FieldDefinitionResponse]


class SetFieldValuesRequest(BaseModel):
    values: Dict[str, Any]


class FieldValuesResponse(BaseModel):
    entity_id: UUID
    schema_version: int
    values: Dict[str, Any]


class FieldValidationErrorDetail(BaseModel):
    path: str
    message: str
    code: str = "invalid"


class FieldValidationErrorResponse(BaseModel):
    message: str = "Field validation failed"
    errors: List[FieldValidationErrorDetail]
