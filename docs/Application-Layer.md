# Application Layer

The application layer defines ports (protocols) and use cases. It depends only on the domain layer.

## Ports

Import from `pkg_dynamic_field.application.ports` or directly from `pkg_dynamic_field`.

### FieldSchemaRepo

```python
class FieldSchemaRepo(Protocol):
    async def get_by_kind(self, kind: str) -> Optional[FieldSchema]: ...
    async def get(self, schema_id: UUID) -> Optional[FieldSchema]: ...
    async def save(self, schema: FieldSchema) -> None: ...
```

### FieldValueRepo

```python
class FieldValueRepo(Protocol):
    async def get_by_entity(self, entity_id: UUID) -> Optional[Tuple[FieldValue, ...]]: ...
    async def save(self, entity_id: UUID, schema_version: int, values: Tuple[FieldValue, ...]) -> None: ...
    async def delete_by_entity(self, entity_id: UUID) -> None: ...
```

### EventBus

```python
class EventBus(Protocol):
    def publish(self, event) -> None: ...
    def publish_many(self, events) -> None: ...
```

### DynamicFieldUoW

```python
class DynamicFieldUoW(Protocol):
    @property
    def field_schemas(self) -> FieldSchemaRepo: ...
    @property
    def field_values(self) -> FieldValueRepo: ...
    @property
    def event_bus(self) -> EventBus: ...

    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, *args) -> None: ...
    async def commit(self) -> None: ...
```

Your existing `AsyncUnitOfWork` satisfies this via duck typing if it exposes `field_schemas`, `field_values`, and `event_bus`.

## DTOs

```python
from pkg_dynamic_field import FieldDefinitionCmd, UpsertFieldSchemaCmd

cmd = UpsertFieldSchemaCmd(
    kind="event",
    definitions=(
        FieldDefinitionCmd(
            key="location",
            type=FieldType.STRING,
            constraints={"required": True, "max_length": 200},
        ),
        FieldDefinitionCmd(
            key="ticket_price",
            type=FieldType.FLOAT,
            constraints={"min": 0},
        ),
    ),
)
```

## Use Cases

### UpsertFieldSchema

Creates a new schema or updates an existing one. Publishes `FieldSchemaCreated` or `FieldSchemaUpdated`.

```python
from pkg_dynamic_field import UpsertFieldSchema

schema = await UpsertFieldSchema(uow).execute(cmd=cmd)
```

### GetFieldSchema

Retrieves a schema by kind. Raises `FieldSchemaNotFoundError` if not found.

```python
from pkg_dynamic_field import GetFieldSchema

schema = await GetFieldSchema(uow).execute(kind="event")
```

### SetFieldValues

Validates values against the schema and saves them. Publishes `FieldValuesSet`. The caller must provide `kind` — this removes any dependency on entity-specific repositories.

```python
from pkg_dynamic_field import SetFieldValues

field_values = await SetFieldValues(uow).execute(
    entity_id=article_id,
    kind="event",
    values={"location": "Dubai", "ticket_price": 50},
)
```

### GetFieldValues

Retrieves stored field values for an entity. Returns `None` if no values exist.

```python
from pkg_dynamic_field import GetFieldValues

values = await GetFieldValues(uow).execute(entity_id=article_id)
# {"location": "Dubai", "ticket_price": 50}
```