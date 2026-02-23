# User Guide

## Key Concepts

### Field Schema

A `FieldSchema` defines the structure of dynamic fields for a given **kind** (a plain string like `"article"`, `"event"`, `"course"`). Each schema has a version number that increments on update.

### Field Definition

A `FieldDefinition` describes a single field within a schema:

- **key**: unique identifier (e.g. `"location"`, `"ticket_price"`)
- **type**: one of `string`, `int`, `float`, `bool`, `date`, `datetime`, `json`, `composite`
- **constraints**: validation rules (`required`, `min`, `max`, `min_length`, `max_length`, `pattern`, `allowed_values`, `min_items`, `max_items`)
- **translatable**: if `true`, value is a dict of locale keys, e.g. `{"en": "Hello", "ar": "مرحبا"}`
- **repeatable**: if `true`, value is a list
- **composite**: contains child definitions, value is a nested object

### Field Value

A `FieldValue` stores a single field's value for a specific entity:

- **entity_id**: the UUID of the entity (article, category, etc.)
- **definition_key**: which field definition this value belongs to
- **value**: the actual data (stored as JSONB)
- **schema_version**: tracks which schema version was used

### Validation

`validate_field_values(schema, raw_values)` checks all values against the schema and returns a list of `FieldError` objects. Supports nested validation for composite, translatable, and repeatable fields.

## Architecture

The package uses clean architecture with three layers:

```
domain/        → Entities, events, exceptions, validation (no dependencies)
application/   → Ports (protocols), DTOs, use cases (depends on domain)
integrations/  → SQLAlchemy + FastAPI adapters (depends on application + domain)
```

### DynamicFieldUoW Protocol

All use cases accept a `DynamicFieldUoW`:

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

Your project's existing async Unit of Work satisfies this via **duck typing** — just ensure it exposes `field_schemas`, `field_values`, and `event_bus` properties.

## Use Cases

| Use Case | Description |
|----------|-------------|
| `UpsertFieldSchema` | Create or update a field schema for a kind |
| `GetFieldSchema` | Retrieve a schema by kind (raises `FieldSchemaNotFoundError` if missing) |
| `SetFieldValues` | Validate and save field values for an entity (requires `kind` parameter) |
| `GetFieldValues` | Retrieve stored field values for an entity |

### Example: Using `SetFieldValues`

```python
from pkg_dynamic_field import SetFieldValues

# The caller provides `kind` — no article/entity repo dependency
field_values = await SetFieldValues(uow).execute(
    entity_id=article.id,
    kind="event",        # plain string, not an enum
    values={"location": "Dubai", "ticket_price": 50},
)
```

## Supported Field Types

| Type | Python Type | Constraints |
|------|------------|-------------|
| `string` | `str` | `min_length`, `max_length`, `pattern`, `allowed_values` |
| `int` | `int` | `min`, `max`, `allowed_values` |
| `float` | `int` or `float` | `min`, `max`, `allowed_values` |
| `bool` | `bool` | — |
| `date` | `str` (ISO format) | — |
| `datetime` | `str` (ISO format) | — |
| `json` | any | — |
| `date_range` | `dict` (`{"start": ..., "end": ...}`) | `range_type` (`"date"` or `"datetime"`) |
| `composite` | `dict` | validated recursively via child definitions |

All types support `required` constraint. Repeatable fields additionally support `min_items` and `max_items`.

## Domain Events

The package publishes events via the `EventBus`:

| Event | When |
|-------|------|
| `FieldSchemaCreated` | A new schema is created |
| `FieldSchemaUpdated` | An existing schema is updated |
| `FieldValuesSet` | Field values are saved for an entity |