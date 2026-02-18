from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    Enum as SAEnum,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...domain.entities import FieldType


def configure_orm(Base, entity_fk="articles.id", entity_column_name="entity_id"):
    """Create and return ORM model classes bound to the given Base and entity FK.

    Args:
        Base: SQLAlchemy DeclarativeBase class.
        entity_fk: Foreign key target for FieldValue.entity_id (e.g. "articles.id").
        entity_column_name: DB column name for the entity FK (e.g. "article_id" for
            backwards compatibility with existing schemas).

    Returns:
        Tuple of (FieldSchemaModel, FieldDefinitionModel, FieldValueModel).
    """
    # Compute constraint/index names based on column name
    uq_name = f"uq_field_value_{entity_column_name.removesuffix('_id')}_key"
    ix_name = f"ix_field_values_{entity_column_name}"

    class FieldSchemaModel(Base):
        __tablename__ = "field_schemas"

        id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        kind: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
        version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
        )

        definitions: Mapped[list["FieldDefinitionModel"]] = relationship(
            back_populates="schema", cascade="all, delete-orphan"
        )

    class FieldDefinitionModel(Base):
        __tablename__ = "field_definitions"

        id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        schema_id: Mapped[UUID] = mapped_column(
            PGUUID(as_uuid=True),
            ForeignKey("field_schemas.id", ondelete="CASCADE"),
            nullable=False,
        )
        parent_id: Mapped[UUID | None] = mapped_column(
            PGUUID(as_uuid=True),
            ForeignKey("field_definitions.id", ondelete="CASCADE"),
            nullable=True,
        )
        key: Mapped[str] = mapped_column(String(255), nullable=False)
        type: Mapped[FieldType] = mapped_column(SAEnum(FieldType, name="field_type"), nullable=False)
        constraints: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
        ui_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
        translatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
        repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
        sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
        group: Mapped[str | None] = mapped_column(String(255), nullable=True)
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
        )

        schema: Mapped[FieldSchemaModel] = relationship("FieldSchemaModel", back_populates="definitions")
        children: Mapped[list["FieldDefinitionModel"]] = relationship(
            back_populates="parent", cascade="all, delete-orphan"
        )
        parent: Mapped["FieldDefinitionModel | None"] = relationship(
            back_populates="children", remote_side=[id]
        )

        __table_args__ = (
            Index(
                "ix_field_definitions_schema_key_top_level",
                "schema_id", "key",
                unique=True,
                postgresql_where="parent_id IS NULL",
            ),
            Index("ix_field_definitions_schema_id", "schema_id"),
        )

    class FieldValueModel(Base):
        __tablename__ = "field_values"

        id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        entity_id: Mapped[UUID] = mapped_column(
            entity_column_name,
            PGUUID(as_uuid=True),
            ForeignKey(entity_fk, ondelete="CASCADE"),
            nullable=False,
        )
        definition_key: Mapped[str] = mapped_column(String(255), nullable=False)
        value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
        schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
        )

        __table_args__ = (
            UniqueConstraint(entity_column_name, "definition_key", name=uq_name),
            Index(ix_name, entity_column_name),
            Index("ix_field_values_value_gin", "value", postgresql_using="gin"),
        )

    return FieldSchemaModel, FieldDefinitionModel, FieldValueModel
