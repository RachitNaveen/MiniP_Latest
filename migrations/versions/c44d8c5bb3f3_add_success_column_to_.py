"""Add success column to FaceVerificationLog

Revision ID: c44d8c5bb3f3
Revises: 678015bc9630
Create Date: 2025-06-03 12:03:40.612600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c44d8c5bb3f3'
down_revision = '678015bc9630'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_user')
    with op.batch_alter_table('face_verification_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('success', sa.Boolean(), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password', sa.VARCHAR(length=128), nullable=False))

    with op.batch_alter_table('face_verification_log', schema=None) as batch_op:
        batch_op.drop_column('success')

    op.create_table('_alembic_tmp_user',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=64), nullable=False),
    sa.Column('face_data', sa.TEXT(), nullable=True),
    sa.Column('last_login', sa.DATETIME(), nullable=True),
    sa.Column('face_verification_enabled', sa.BOOLEAN(), nullable=True),
    sa.Column('face_verification_failed_attempts', sa.INTEGER(), nullable=True),
    sa.Column('face_verification_locked_until', sa.DATETIME(), nullable=True),
    sa.Column('password_hash', sa.VARCHAR(length=128), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    # ### end Alembic commands ###
