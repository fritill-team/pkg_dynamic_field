# FastAPI Integration

Provides Pydantic schemas, a route factory, and error handlers.

## Error Handlers

Install field-specific exception handlers on your FastAPI app:

```python
from pkg_dynamic_field.integrations.fastapi import install_field_error_handlers

app = FastAPI()
install_field_error_handlers(app)
```

This registers:

| Exception | HTTP Status | Response |
|-----------|-------------|----------|
| `FieldSchemaNotFoundError` | 404 | `{"detail": "No field schema found for kind '...'"}` |
| `FieldValidationError` | 422 | `{"message": "Field validation failed", "errors": [...]}` |

## Pydantic Schemas

```python
from pkg_dynamic_field.integrations.fastapi.schemas import (
    FieldDefinitionInput,       # Request: create/update definition
    UpsertFieldSchemaRequest,   # Request: upsert schema
    SetFieldValuesRequest,      # Request: set values
    FieldDefinitionResponse,    # Response: definition (recursive)
    FieldSchemaResponse,        # Response: schema with definitions
    FieldValuesResponse,        # Response: entity field values
    FieldValidationErrorDetail, # Error detail item
    FieldValidationErrorResponse, # Full error response
)
```

### Key Response Models

```python
class FieldSchemaResponse(BaseModel):
    id: UUID
    kind: str          # plain string, not an enum
    version: int
    definitions: List[FieldDefinitionResponse]

class FieldValuesResponse(BaseModel):
    entity_id: UUID    # generic, not article_id
    schema_version: int
    values: Dict[str, Any]
```

## Route Factory

`create_field_routers()` generates two routers with full CRUD wired to the package use cases:

```python
from pkg_dynamic_field.integrations.fastapi.routes import create_field_routers

schema_router, entity_fields_router = create_field_routers(
    get_uow=get_uow,           # FastAPI Depends for your UoW
    require_auth=authn.get_current_user,   # Depends for authenticated user
    require_admin=authn.require_realm_roles("admin"),  # Depends for admin
    schema_prefix="/field-schemas",
    schema_tags=["field-schemas"],
    entity_prefix="/articles",
    entity_tags=["article-fields"],
)

app.include_router(schema_router)
app.include_router(entity_fields_router)
```

### Generated Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/{kind}` | `require_auth` | Get schema by kind |
| `PUT` | `/{kind}` | `require_admin` | Create or update schema |
| `GET` | `/{entity_id}/fields` | `require_auth` | Get entity field values |
| `PUT` | `/{entity_id}/fields?kind=...` | `require_auth` | Set entity field values |

## Custom Routes (instead of factory)

If you need more control (e.g. fetching an article to get its kind), write routes directly using the use cases:

```python
from fastapi import APIRouter, Depends
from pkg_dynamic_field import SetFieldValues, GetFieldValues, GetFieldSchema, UpsertFieldSchema

router = APIRouter()

@router.put("/articles/{article_id}/fields")
async def set_article_field_values(
    article_id: UUID,
    payload: SetFieldValuesRequest,
    uow = Depends(get_uow),
    current_user = Depends(require_auth),
):
    # Fetch article to determine kind
    async with uow:
        article = await uow.articles.get(article_id)

    field_values = await SetFieldValues(uow).execute(
        entity_id=article_id,
        kind=article.kind.value,  # map your enum to str
        values=payload.values,
    )
    return FieldValuesResponse(
        entity_id=article_id,
        schema_version=field_values[0].schema_version if field_values else 0,
        values={fv.definition_key: fv.value for fv in field_values},
    )
```

This is the recommended approach when `kind` is derived from the entity itself (like `ArticleKind`).