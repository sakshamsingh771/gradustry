"""add skill_ratings provenance to industry_feedback

Revision ID: 7c2d4e9f1a33
Revises: 3e8f5a1c9b02
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op  # pyright: ignore[reportAttributeAccessIssue]
import sqlalchemy as sa


revision: str = '7c2d4e9f1a33'
down_revision: Union[str, None] = '3e8f5a1c9b02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('industry_feedback', schema=None) as batch_op:
        batch_op.add_column(sa.Column('skill_ratings', sa.JSON(), nullable=False, server_default='[]'))

    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('application_deadline', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.drop_column('application_deadline')

    with op.batch_alter_table('industry_feedback', schema=None) as batch_op:
        batch_op.drop_column('skill_ratings')
