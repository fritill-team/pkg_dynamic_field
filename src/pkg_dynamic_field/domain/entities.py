from __future__ import annotations

import enum
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Optional, Tuple
from uuid import UUID


class FieldType(str, enum.Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    DATE_RANGE = "date_range"
    COMPOSITE = "composite"


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    id: UUID
    schema_id: UUID
    key: str
    type: FieldType
    parent_id: Optional[UUID] = None
    constraints: dict = field(default_factory=dict)
    ui_config: dict = field(default_factory=dict)
    translatable: bool = False
    repeatable: bool = False
    sort_order: int = 0
    group: Optional[str] = None
    _children: Tuple[FieldDefinition, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        schema_id: UUID,
        key: str,
        type: FieldType,
        parent_id: Optional[UUID] = None,
        constraints: Optional[dict] = None,
        ui_config: Optional[dict] = None,
        translatable: bool = False,
        repeatable: bool = False,
        sort_order: int = 0,
        group: Optional[str] = None,
        children: Tuple[FieldDefinition, ...] = (),
    ) -> FieldDefinition:
        return cls(
            id=id,
            schema_id=schema_id,
            key=key,
            type=type,
            parent_id=parent_id,
            constraints=constraints or {},
            ui_config=ui_config or {},
            translatable=translatable,
            repeatable=repeatable,
            sort_order=sort_order,
            group=group,
            _children=children,
        )

    @property
    def children(self) -> Tuple[FieldDefinition, ...]:
        return self._children

    def with_children(self, children: Tuple[FieldDefinition, ...]) -> FieldDefinition:
        return replace(self, _children=children)


@dataclass(frozen=True, slots=True)
class FieldSchema:
    id: UUID
    kind: str
    version: int = 1
    _definitions: Tuple[FieldDefinition, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        kind: str,
        version: int = 1,
        definitions: Tuple[FieldDefinition, ...] = (),
    ) -> FieldSchema:
        now = datetime.now(timezone.utc)
        return cls(
            id=id,
            kind=kind,
            version=version,
            _definitions=definitions,
            created_at=now,
            updated_at=now,
        )

    @property
    def definitions(self) -> Tuple[FieldDefinition, ...]:
        return self._definitions

    @property
    def top_level_definitions(self) -> Tuple[FieldDefinition, ...]:
        return tuple(d for d in self._definitions if d.parent_id is None)

    def get_definition(self, key: str) -> Optional[FieldDefinition]:
        for d in self._definitions:
            if d.key == key:
                return d
        return None

    def with_definitions(self, definitions: Tuple[FieldDefinition, ...]) -> FieldSchema:
        return replace(
            self,
            _definitions=definitions,
            version=self.version + 1,
            updated_at=datetime.now(timezone.utc),
        )


@dataclass(frozen=True, slots=True)
class FieldValue:
    id: UUID
    entity_id: UUID
    definition_key: str
    value: Any
    schema_version: int = 1
