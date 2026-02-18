# SQLAlchemy Integration

Provides a `configure_orm()` factory to create ORM models bound to your project's `Base` and FK target, plus repository implementations.

## `configure_orm()`

```python
from pkg_dynamic_field.integrations.sqlalchemy import configure_orm
from your_project.database.orm.base import Base

FieldSchemaModel, FieldDefinitionModel, FieldValueModel = configure_orm(
    Base,
    entity_fk="articles.id",          # FK target for FieldValue
    entity_column_name="article_id",   # DB column name (default: "entity_id")
)
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Base` | (required) | Your SQLAlchemy `DeclarativeBase` class |
| `entity_fk` | `"articles.id"` | Foreign key target for the entity column |
| `entity_column_name` | `"entity_id"` | Actual DB column name for the FK |

### Why `entity_column_name`?

The domain entity uses `entity_id` (generic), but your database may already have `article_id` as the column name. This parameter lets you keep the existing DB schema without a migration:

```python
# Maps Python attribute `entity_id` → DB column `article_id`
configure_orm(Base, entity_fk="articles.id", entity_column_name="article_id")
```

### Generated Tables

| Table | Columns |
|-------|---------|
| `field_schemas` | `id`, `kind` (unique), `version`, `created_at`, `updated_at` |
| `field_definitions` | `id`, `schema_id` (FK), `parent_id` (FK, self-ref), `key`, `type`, `constraints`, `ui_config`, `translatable`, `repeatable`, `sort_order`, `group`, `created_at`, `updated_at` |
| `field_values` | `id`, `entity_id`/custom column, `definition_key`, `value` (JSONB), `schema_version`, `created_at`, `updated_at` |

### Examples by Project

```python
# itq_articles — fields on articles, existing "article_id" column
configure_orm(Base, entity_fk="articles.id", entity_column_name="article_id")

# itq_taxonomy — fields on categories
configure_orm(Base, entity_fk="categories.id", entity_column_name="category_id")

# New project — use defaults
configure_orm(Base, entity_fk="products.id")
# column name defaults to "entity_id"
```

## Repositories

```python
from pkg_dynamic_field.integrations.sqlalchemy import (
    SQLAlchemyFieldSchemaRepo,
    SQLAlchemyFieldValueRepo,
)
```

### SQLAlchemyFieldSchemaRepo

```python
repo = SQLAlchemyFieldSchemaRepo(
    session,
    schema_model=FieldSchemaModel,
    definition_model=FieldDefinitionModel,
)

schema = await repo.get_by_kind("event")
schema = await repo.get(schema_id)
await repo.save(schema)
```

### SQLAlchemyFieldValueRepo

```python
repo = SQLAlchemyFieldValueRepo(session, value_model=FieldValueModel)

values = await repo.get_by_entity(entity_id)
await repo.save(entity_id=entity_id, schema_version=1, values=field_values)
await repo.delete_by_entity(entity_id)
```

## Wiring in Your UoW

Example: wrapping the package repos so they auto-inject ORM models.

```python
# infra/database/repositories/fields.py
from pkg_dynamic_field.integrations.sqlalchemy.repositories import (
    SQLAlchemyFieldSchemaRepo as _PkgSchemaRepo,
    SQLAlchemyFieldValueRepo as _PkgValueRepo,
)
from your_project.database.orm.fields import (
    FieldSchemaModel, FieldDefinitionModel, FieldValueModel,
)

class SQLAlchemyFieldSchemaRepo(_PkgSchemaRepo):
    def __init__(self, session):
        super().__init__(session, schema_model=FieldSchemaModel, definition_model=FieldDefinitionModel)

class SQLAlchemyFieldValueRepo(_PkgValueRepo):
    def __init__(self, session):
        super().__init__(session, value_model=FieldValueModel)
```

Then in your UoW:

```python
@property
def field_schemas(self):
    if self._field_schemas is None:
        self._field_schemas = SQLAlchemyFieldSchemaRepo(self._session)
    return self._field_schemas

@property
def field_values(self):
    if self._field_values is None:
        self._field_values = SQLAlchemyFieldValueRepo(self._session)
    return self._field_values
```