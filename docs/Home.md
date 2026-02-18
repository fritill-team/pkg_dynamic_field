# Welcome to pkg-dynamic-field

`pkg-dynamic-field` is an entity-agnostic package for dynamic field definitions, validation, and value storage. It follows clean architecture (Hexagonal / Ports & Adapters) and can be plugged into any Python project.

## What It Does

- Define **field schemas** per entity kind (e.g. "article", "event", "course")
- Each schema contains **field definitions** with types, constraints, and nesting (composite fields)
- **Validate** user-submitted values against a schema
- **Store** field values per entity with schema versioning
- Works with **any entity** — articles, categories, products, etc.

## Getting Started

- **[Installation](Installation)**: Install `pkg-dynamic-field` in your project.
- **[User Guide](User-Guide)**: Understand key concepts and the overall architecture.

## Integrations

- **[SQLAlchemy Integration](SQLAlchemy-Integration)**: ORM models and repository implementations.
- **[FastAPI Integration](FastAPI-Integration)**: Pydantic schemas, route factories, and error handlers.

## Architecture

```
pkg_dynamic_field/
├── domain/           # Entities, events, exceptions, validation
├── application/      # Ports (protocols), DTOs, use cases
└── integrations/
    ├── sqlalchemy/   # ORM factory + repositories
    └── fastapi/      # Schemas, routes factory, error handlers
```

The package defines its own `DynamicFieldUoW` protocol. Your project's existing Unit of Work satisfies it via duck typing — no adapter needed.
