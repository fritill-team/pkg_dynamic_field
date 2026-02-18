# Domain Layer

The domain layer has zero external dependencies. It contains all business logic for dynamic fields.

## Entities

Import from `pkg_dynamic_field.domain.entities` or directly from `pkg_dynamic_field`.

### FieldType

```python
class FieldType(str, Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    COMPOSITE = "composite"
```

### FieldDefinition

Frozen dataclass representing a single field definition.

```python
defn = FieldDefinition.create(
    id=uuid4(),
    schema_id=schema_id,
    key="ticket_price",
    type=FieldType.FLOAT,
    constraints={"required": True, "min": 0},
    ui_config={"widget": "currency"},
    sort_order=1,
    group="pricing",
)

# Composite fields have children
composite = FieldDefinition.create(
    id=uuid4(),
    schema_id=schema_id,
    key="address",
    type=FieldType.COMPOSITE,
    children=(street_def, city_def, zip_def),
)
```

### FieldSchema

Frozen dataclass. The aggregate root for field definitions.

```python
schema = FieldSchema.create(
    id=uuid4(),
    kind="event",          # plain str, not an enum
    version=1,
    definitions=(defn1, defn2),
)

# Access definitions
schema.definitions          # all definitions (flat)
schema.top_level_definitions  # only root-level (no children)
schema.get_definition("ticket_price")  # by key

# Immutable update
new_schema = schema.with_definitions(new_defs)  # bumps version
```

### FieldValue

```python
fv = FieldValue(
    id=uuid4(),
    entity_id=article_id,  # any entity UUID
    definition_key="ticket_price",
    value=50.0,
    schema_version=1,
)
```

## Validation

```python
from pkg_dynamic_field import validate_field_values

errors = validate_field_values(schema, {"ticket_price": -5})
# errors = [FieldError(path="ticket_price", message="Value must be >= 0.", code="min")]
```

Returns a list of `FieldError` objects (not exceptions). Raise `FieldValidationError(errors)` if the list is non-empty.

## Exceptions

| Class | Type | Usage |
|-------|------|-------|
| `FieldError` | Data carrier (not an Exception) | Single validation failure |
| `FieldSchemaNotFoundError` | Exception | No schema for the given kind |
| `FieldValidationError` | Exception | Contains a list of `FieldError` |

## Events

All events extend the package's own `DomainEvent` base (same shape as most project-level domain events):

```python
@dataclass(slots=True)
class DomainEvent:
    event_id: UUID
    occurred_at: datetime
    aggregate_type: str
    aggregate_id: UUID | None
    metadata: Mapping[str, Any] | None
```

| Event | `aggregate_type` | Extra Fields |
|-------|-----------------|--------------|
| `FieldSchemaCreated` | `"field_schema"` | `kind`, `version` |
| `FieldSchemaUpdated` | `"field_schema"` | `kind`, `version` |
| `FieldValuesSet` | `"entity"` | `schema_version` |