from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities import (
    FieldDefinition,
    FieldSchema,
    FieldType,
    FieldValue,
)


class SQLAlchemyFieldSchemaRepo:

    def __init__(self, session: AsyncSession, *, schema_model, definition_model):
        self._session = session
        self._schema_model = schema_model
        self._definition_model = definition_model

    async def get_by_kind(self, kind: str) -> Optional[FieldSchema]:
        stmt = select(self._schema_model).where(self._schema_model.kind == kind)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return await self._hydrate(model)

    async def get(self, schema_id: UUID) -> Optional[FieldSchema]:
        model = await self._session.get(self._schema_model, schema_id)
        if model is None:
            return None
        return await self._hydrate(model)

    async def save(self, schema: FieldSchema) -> None:
        with self._session.no_autoflush:
            model = await self._session.get(self._schema_model, schema.id)
            if model is None:
                model = self._schema_model(id=schema.id)
                self._session.add(model)

            model.kind = schema.kind
            model.version = schema.version

            await self._session.execute(
                delete(self._definition_model).where(
                    self._definition_model.schema_id == schema.id
                )
            )

            for defn in schema.definitions:
                self._session.add(
                    self._definition_model(
                        id=defn.id,
                        schema_id=schema.id,
                        parent_id=defn.parent_id,
                        key=defn.key,
                        type=defn.type,
                        constraints=defn.constraints or None,
                        ui_config=defn.ui_config or None,
                        translatable=defn.translatable,
                        repeatable=defn.repeatable,
                        sort_order=defn.sort_order,
                        group=defn.group,
                    )
                )

        await self._session.flush()

    async def _hydrate(self, model) -> FieldSchema:
        stmt = (
            select(self._definition_model)
            .where(self._definition_model.schema_id == model.id)
            .order_by(self._definition_model.sort_order)
        )
        rows = (await self._session.execute(stmt)).scalars().all()

        flat_defs = [_definition_to_entity(row) for row in rows]
        _assemble_definition_tree(flat_defs)

        return FieldSchema.create(
            id=model.id,
            kind=model.kind,
            version=model.version,
            definitions=tuple(flat_defs),
        )


def _definition_to_entity(model) -> FieldDefinition:
    return FieldDefinition.create(
        id=model.id,
        schema_id=model.schema_id,
        key=model.key,
        type=model.type,
        parent_id=model.parent_id,
        constraints=model.constraints or {},
        ui_config=model.ui_config or {},
        translatable=model.translatable,
        repeatable=model.repeatable,
        sort_order=model.sort_order,
        group=model.group,
    )


def _assemble_definition_tree(
    flat_defs: List[FieldDefinition],
) -> List[FieldDefinition]:
    """Build tree: populates _children on COMPOSITE definitions."""
    by_id: Dict[UUID, FieldDefinition] = {d.id: d for d in flat_defs}
    children_map: Dict[Optional[UUID], List[FieldDefinition]] = {}

    for d in flat_defs:
        children_map.setdefault(d.parent_id, []).append(d)

    def _build(parent_id: Optional[UUID]) -> List[FieldDefinition]:
        result = []
        for child in children_map.get(parent_id, []):
            if child.type == FieldType.COMPOSITE:
                grandchildren = _build(child.id)
                child = child.with_children(tuple(grandchildren))
            result.append(child)
        return result

    return _build(None)


class SQLAlchemyFieldValueRepo:

    def __init__(self, session: AsyncSession, *, value_model):
        self._session = session
        self._value_model = value_model

    async def get_by_entity(self, entity_id: UUID) -> Optional[Tuple[FieldValue, ...]]:
        stmt = select(self._value_model).where(self._value_model.entity_id == entity_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        if not rows:
            return None
        return tuple(
            FieldValue(
                id=row.id,
                entity_id=row.entity_id,
                definition_key=row.definition_key,
                value=row.value,
                schema_version=row.schema_version,
            )
            for row in rows
        )

    async def save(
        self,
        entity_id: UUID,
        schema_version: int,
        values: Tuple[FieldValue, ...],
    ) -> None:
        with self._session.no_autoflush:
            await self._session.execute(
                delete(self._value_model).where(self._value_model.entity_id == entity_id)
            )
            for fv in values:
                self._session.add(
                    self._value_model(
                        id=fv.id,
                        entity_id=entity_id,
                        definition_key=fv.definition_key,
                        value=fv.value,
                        schema_version=schema_version,
                    )
                )
        await self._session.flush()

    async def delete_by_entity(self, entity_id: UUID) -> None:
        await self._session.execute(
            delete(self._value_model).where(self._value_model.entity_id == entity_id)
        )


__all__ = [
    "SQLAlchemyFieldSchemaRepo",
    "SQLAlchemyFieldValueRepo",
]
