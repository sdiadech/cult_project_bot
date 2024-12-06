"""

Revision ID: 4978fe77a868
Revises: 
Create Date: 2024-12-04 18:16:07.880307

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4978fe77a868"
down_revision: Union[str, None] = None


def upgrade() -> None:
    """
    Apply the migration: `payments` tables.
    """

    # Create `payments` table
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False),
        sa.Column("user_name", sa.String, nullable=False),
        sa.Column("course_name", sa.String, nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("status", sa.String, nullable=False),
    )


def downgrade() -> None:
    """
    Revert the migration: Drop `users` and `payments` tables.
    """
    # Drop `payments` table
    op.drop_table("payments")
