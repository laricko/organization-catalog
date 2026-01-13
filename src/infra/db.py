import os

from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://catalog:catalog@localhost:5432/catalog",
)


engine = create_async_engine(DATABASE_URL)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

metadata = MetaData()

buildings = Table(
    "buildings",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("address", String, nullable=False),
    Column("lat", Float, nullable=False),
    Column("lon", Float, nullable=False),
)

activities = Table(
    "activities",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("name", String, nullable=False),
    Column("parent_id", UUID(as_uuid=True), ForeignKey("activities.id"), nullable=True),
    Column("level", Integer, nullable=False),
    CheckConstraint("level in (1, 2, 3)", name="ck_activity_level"),
)

organizations = Table(
    "organizations",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("name", String, nullable=False),
    Column(
        "building_id",
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="RESTRICT"),
        nullable=False,
    ),
)


organization_activities = Table(
    "organization_activities",
    metadata,
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "activity_id",
        UUID(as_uuid=True),
        ForeignKey("activities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


organization_phones = Table(
    "organization_phones",
    metadata,
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("phone", String, primary_key=True),
)
