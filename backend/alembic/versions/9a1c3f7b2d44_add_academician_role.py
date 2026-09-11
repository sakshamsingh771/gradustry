"""add academician role, profile, and opportunity/application audience support

Revision ID: 9a1c3f7b2d44
Revises: fa7ea7063e55
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1c3f7b2d44'
down_revision: Union[str, None] = 'fa7ea7063e55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- New table: academician_profiles ---
    op.create_table(
        'academician_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('college_id', sa.Integer(), nullable=True),
        sa.Column('designation', sa.String(length=255), nullable=False),
        sa.Column('institution', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=False),
        sa.Column('area_of_expertise', sa.String(length=500), nullable=False),
        sa.Column('experience_years', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['college_id'], ['college_profiles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_academician_profiles_user_id'), 'academician_profiles', ['user_id'], unique=True)

    # --- opportunities: add `audience` column (student|academician) ---
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('audience', sa.String(length=20), nullable=False, server_default='student'))
    op.create_index(op.f('ix_opportunities_audience'), 'opportunities', ['audience'], unique=False)

    # --- applications: student_id becomes nullable, add academician_id ---
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.alter_column('student_id', existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column('academician_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_applications_academician_id', 'academician_profiles', ['academician_id'], ['id']
        )
    op.create_index(op.f('ix_applications_academician_id'), 'applications', ['academician_id'], unique=False)
    

def downgrade() -> None:
    op.drop_index(op.f('ix_applications_academician_id'), table_name='applications')
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_constraint('fk_applications_academician_id', type_='foreignkey')
        batch_op.drop_column('academician_id')
        batch_op.alter_column('student_id', existing_type=sa.Integer(), nullable=False)

    op.drop_index(op.f('ix_opportunities_audience'), table_name='opportunities')
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.drop_column('audience')

    op.drop_index(op.f('ix_academician_profiles_user_id'), table_name='academician_profiles')
    op.drop_table('academician_profiles')
