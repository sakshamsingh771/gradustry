"""add learning hub fields (duration, capacity, eligibility_notes) to opportunities

Revision ID: 3e8f5a1c9b02
Revises: 9a1c3f7b2d44
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op  # pyright: ignore[reportAttributeAccessIssue]
import sqlalchemy as sa


revision: str = '3e8f5a1c9b02'
down_revision: Union[str, None] = '9a1c3f7b2d44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('capacity', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('eligibility_notes', sa.Text(), nullable=False, server_default=''))


def downgrade() -> None:
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.drop_column('eligibility_notes')
        batch_op.drop_column('capacity')
        batch_op.drop_column('duration')
