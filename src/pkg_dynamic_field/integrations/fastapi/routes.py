from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Depends

from ...application.dtos import FieldDefinitionCmd, UpsertFieldSchemaCmd
from ...application.use_cases import GetFieldSchema, GetFieldValues, SetFieldValues, UpsertFieldSchema
from .schemas import (
    FieldDefinitionInput,
    FieldDefinitionResponse,
    FieldSchemaResponse,
    FieldValuesResponse,
    SetFieldValuesRequest,
    UpsertFieldSchemaRequest,
)


def create_field_routers(
    *,
    get_uow: Callable,
    require_auth: Callable,
    require_admin: Callable,
    schema_prefix: str = "/field-schemas",
    schema_tags: list[str] | None = None,
    entity_prefix: str = "",
    entity_tags: list[str] | None = None,
):
    """Create FastAPI routers for field schema management and entity field values.

    Args:
        get_uow: FastAPI dependency that provides a DynamicFieldUoW.
        require_auth: FastAPI dependency for authenticated user.
        require_admin: FastAPI dependency for admin-level access.
        schema_prefix: URL prefix for schema management routes.
        schema_tags: OpenAPI tags for schema routes.
        entity_prefix: URL prefix for entity field value routes.
        entity_tags: OpenAPI tags for entity field value routes.

    Returns:
        Tuple of (schema_router, entity_fields_router).
    """
    schema_router = APIRouter(prefix=schema_prefix, tags=schema_tags or ["field-schemas"])
    entity_fields_router = APIRouter(prefix=entity_prefix, tags=entity_tags or ["entity-fields"])

    # ---- Schema management ----

    @schema_router.get("/{kind}", response_model=FieldSchemaResponse)
    async def get_field_schema(
        kind: str,
        uow=Depends(get_uow),
        current_user=Depends(require_auth),
    ):
        schema = await GetFieldSchema(uow).execute(kind=kind)
        return _schema_to_response(schema)

    @schema_router.put("/{kind}", response_model=FieldSchemaResponse)
    async def upsert_field_schema(
        kind: str,
        payload: UpsertFieldSchemaRequest,
        uow=Depends(get_uow),
        current_user=Depends(require_admin),
    ):
        cmd = UpsertFieldSchemaCmd(
            kind=kind,
            definitions=tuple(_input_to_cmd(d) for d in payload.definitions),
        )
        schema = await UpsertFieldSchema(uow).execute(cmd=cmd)
        return _schema_to_response(schema)

    # ---- Entity field values ----

    @entity_fields_router.get("/{entity_id}/fields", response_model=FieldValuesResponse)
    async def get_entity_field_values(
        entity_id: UUID,
        uow=Depends(get_uow),
        current_user=Depends(require_auth),
    ):
        values = await GetFieldValues(uow).execute(entity_id=entity_id)
        return FieldValuesResponse(
            entity_id=entity_id,
            schema_version=0,
            values=values or {},
        )

    @entity_fields_router.put("/{entity_id}/fields", response_model=FieldValuesResponse)
    async def set_entity_field_values(
        entity_id: UUID,
        kind: str,
        payload: SetFieldValuesRequest,
        uow=Depends(get_uow),
        current_user=Depends(require_auth),
    ):
        field_values = await SetFieldValues(uow).execute(
            entity_id=entity_id,
            kind=kind,
            values=payload.values,
        )
        schema_version = field_values[0].schema_version if field_values else 0
        return FieldValuesResponse(
            entity_id=entity_id,
            schema_version=schema_version,
            values={fv.definition_key: fv.value for fv in field_values},
        )

    return schema_router, entity_fields_router


# ---- Mappers ----


def _input_to_cmd(inp: FieldDefinitionInput) -> FieldDefinitionCmd:
    return FieldDefinitionCmd(
        key=inp.key,
        type=inp.type,
        constraints=inp.constraints,
        ui_config=inp.ui_config,
        translatable=inp.translatable,
        repeatable=inp.repeatable,
        sort_order=inp.sort_order,
        group=inp.group,
        children=tuple(_input_to_cmd(c) for c in inp.children),
    )


def _schema_to_response(schema) -> FieldSchemaResponse:
    top_level = [d for d in schema.definitions if d.parent_id is None]
    children_map: dict = {}
    for d in schema.definitions:
        if d.parent_id is not None:
            children_map.setdefault(d.parent_id, []).append(d)

    def _def_to_response(defn) -> FieldDefinitionResponse:
        kids = children_map.get(defn.id, [])
        return FieldDefinitionResponse(
            id=defn.id,
            key=defn.key,
            type=defn.type,
            parent_id=defn.parent_id,
            constraints=defn.constraints,
            ui_config=defn.ui_config,
            translatable=defn.translatable,
            repeatable=defn.repeatable,
            sort_order=defn.sort_order,
            group=defn.group,
            children=[_def_to_response(c) for c in kids],
        )

    return FieldSchemaResponse(
        id=schema.id,
        kind=schema.kind,
        version=schema.version,
        definitions=[_def_to_response(d) for d in top_level],
    )
