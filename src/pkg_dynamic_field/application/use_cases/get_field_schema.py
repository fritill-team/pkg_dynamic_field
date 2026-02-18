from __future__ import annotations

from ..ports import DynamicFieldUoW
from ...domain.entities import FieldSchema
from ...domain.exceptions import FieldSchemaNotFoundError


class GetFieldSchema:

    def __init__(self, uow: DynamicFieldUoW) -> None:
        self.uow = uow

    async def execute(self, *, kind: str) -> FieldSchema:
        async with self.uow:
            schema = await self.uow.field_schemas.get_by_kind(kind)
            if schema is None:
                raise FieldSchemaNotFoundError(kind=kind)
            return schema
