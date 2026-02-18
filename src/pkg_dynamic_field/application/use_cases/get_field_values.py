from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from ..ports import DynamicFieldUoW


class GetFieldValues:

    def __init__(self, uow: DynamicFieldUoW) -> None:
        self.uow = uow

    async def execute(self, *, entity_id: UUID) -> Optional[Dict[str, Any]]:
        async with self.uow:
            field_values = await self.uow.field_values.get_by_entity(entity_id)
            if not field_values:
                return None
            return {fv.definition_key: fv.value for fv in field_values}
