from __future__ import annotations

from typing import List, Tuple
from uuid import uuid4

from ..dtos import FieldDefinitionCmd, UpsertFieldSchemaCmd
from ..ports import DynamicFieldUoW
from ...domain.entities import FieldDefinition, FieldSchema
from ...domain.events import FieldSchemaCreated, FieldSchemaUpdated


class UpsertFieldSchema:

    def __init__(self, uow: DynamicFieldUoW) -> None:
        self.uow = uow

    async def execute(self, *, cmd: UpsertFieldSchemaCmd) -> FieldSchema:
        async with self.uow:
            existing = await self.uow.field_schemas.get_by_kind(cmd.kind)

            if existing:
                schema_id = existing.id
                version = existing.version + 1
            else:
                schema_id = uuid4()
                version = 1

            flat_defs = self._flatten_definitions(
                schema_id=schema_id,
                cmds=cmd.definitions,
                parent_id=None,
            )

            schema = FieldSchema.create(
                id=schema_id,
                kind=cmd.kind,
                version=version,
                definitions=tuple(flat_defs),
            )

            await self.uow.field_schemas.save(schema)

            if existing:
                self.uow.event_bus.publish(
                    FieldSchemaUpdated(
                        aggregate_id=schema.id,
                        kind=schema.kind,
                        version=schema.version,
                    )
                )
            else:
                self.uow.event_bus.publish(
                    FieldSchemaCreated(
                        aggregate_id=schema.id,
                        kind=schema.kind,
                        version=schema.version,
                    )
                )

            await self.uow.commit()
            return schema

    def _flatten_definitions(
        self,
        *,
        schema_id,
        cmds: Tuple[FieldDefinitionCmd, ...],
        parent_id,
    ) -> List[FieldDefinition]:
        result: List[FieldDefinition] = []
        for i, cmd in enumerate(cmds):
            def_id = uuid4()
            defn = FieldDefinition.create(
                id=def_id,
                schema_id=schema_id,
                key=cmd.key,
                type=cmd.type,
                parent_id=parent_id,
                constraints=cmd.constraints,
                ui_config=cmd.ui_config,
                translatable=cmd.translatable,
                repeatable=cmd.repeatable,
                sort_order=cmd.sort_order or i,
                group=cmd.group,
            )
            result.append(defn)

            if cmd.children:
                children = self._flatten_definitions(
                    schema_id=schema_id,
                    cmds=cmd.children,
                    parent_id=def_id,
                )
                result.extend(children)

        return result
