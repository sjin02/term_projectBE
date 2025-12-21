"""replace is_deleted with deleted_at

Revision ID: d27851868771
Revises: 75f24f0ebdb1
Create Date: 2025-12-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d27851868771"
down_revision: Union[str, Sequence[str], None] = "75f24f0ebdb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # contents
    op.add_column(
        "contents",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.drop_column("contents", "is_deleted")

    # genres
    op.add_column(
        "genres",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.drop_column("genres", "is_deleted")

    # users
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    # users
    op.drop_column("users", "deleted_at")

    # genres
    op.add_column(
        "genres",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_column("genres", "deleted_at")

    # contents
    op.add_column(
        "contents",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_column("contents", "deleted_at")
