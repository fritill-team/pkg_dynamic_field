from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from ..domain.entities import FieldType


@dataclass(frozen=True, slots=True)
class FieldDefinitionCmd:
    key: str
    type: FieldType
    constraints: dict = field(default_factory=dict)
    ui_config: dict = field(default_factory=dict)
    translatable: bool = False
    repeatable: bool = False
    sort_order: int = 0
    group: Optional[str] = None
    children: Tuple[FieldDefinitionCmd, ...] = ()


@dataclass(frozen=True, slots=True)
class UpsertFieldSchemaCmd:
    kind: str
    definitions: Tuple[FieldDefinitionCmd, ...]
