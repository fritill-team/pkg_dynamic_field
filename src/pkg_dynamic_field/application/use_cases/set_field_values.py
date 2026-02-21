from __future__ import annotations

from typing import Any, Dict, Tuple
from uuid import UUID, uuid4

from ..ports import DynamicFieldUoW
from ...domain.entities import FieldValue
from ...domain.events import FieldValuesSet
from ...domain.exceptions import FieldSchemaNotFoundError, FieldValidationError
from ...domain.validation import validate_field_values


class SetFieldValues:

    def __init__(self, uow: DynamicFieldUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        *,
        entity_id: UUID,
        kind: str,
        values: Dict[str, Any],
    ) -> Tuple[FieldValue, ...]:
        async with self.uow:
            schema = await self.uow.field_schemas.get_by_kind(kind)
            if schema is None:
                raise FieldSchemaNotFoundError(kind=kind)

            errors = validate_field_values(schema, values)
            if errors:
                for e in errors:
                    print(f"  FIELD_VALIDATION_DEBUG: path={e.path} message={e.message} code={e.code}")
                raise FieldValidationError(errors=errors)

            known_keys = {d.key for d in schema.top_level_definitions}
            field_values = tuple(
                FieldValue(
                    id=uuid4(),
                    entity_id=entity_id,
                    definition_key=key,
                    value=val,
                    schema_version=schema.version,
                )
                for key, val in values.items()
                if key in known_keys
            )

            await self.uow.field_values.save(
                entity_id=entity_id,
                schema_version=schema.version,
                values=field_values,
            )

            self.uow.event_bus.publish(
                FieldValuesSet(
                    aggregate_id=entity_id,
                    schema_version=schema.version,
                )
            )

            await self.uow.commit()
            return field_values
