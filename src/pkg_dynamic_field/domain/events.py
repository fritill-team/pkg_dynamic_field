from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID, uuid4


@dataclass(slots=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_type: str = ""
    aggregate_id: UUID | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(slots=True)
class FieldSchemaCreated(DomainEvent):
    aggregate_type: str = "field_schema"
    aggregate_id: UUID | None = None

    kind: str | None = None
    version: int | None = None


@dataclass(slots=True)
class FieldSchemaUpdated(DomainEvent):
    aggregate_type: str = "field_schema"
    aggregate_id: UUID | None = None

    kind: str | None = None
    version: int | None = None


@dataclass(slots=True)
class FieldValuesSet(DomainEvent):
    aggregate_type: str = "entity"
    aggregate_id: UUID | None = None

    schema_version: int | None = None
