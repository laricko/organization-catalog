"""Add tables

Revision ID: d6f2b9b52c02
Revises:
Create Date: 2026-01-13 22:53:53.720632

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d6f2b9b52c02"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "activities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.CheckConstraint("level in (1, 2, 3)", name="ck_activity_level"),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["activities.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "buildings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("building_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "organization_activities",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("activity_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("organization_id", "activity_id"),
    )
    op.create_table(
        "organization_phones",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("organization_id", "phone"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("organization_phones")
    op.drop_table("organization_activities")
    op.drop_table("organizations")
    op.drop_table("buildings")
    op.drop_table("activities")
