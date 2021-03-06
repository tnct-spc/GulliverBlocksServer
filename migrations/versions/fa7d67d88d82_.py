"""empty message

Revision ID: fa7d67d88d82
Revises: 7f922a2057ea
Create Date: 2019-08-23 13:09:14.747341

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fa7d67d88d82'
down_revision = '7f922a2057ea'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('block', sa.Column('pattern_group_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('block', sa.Column('pattern_name', sa.String(), nullable=True))
    op.create_foreign_key(None, 'block', 'pattern', ['pattern_name'], ['name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'block', type_='foreignkey')
    op.drop_column('block', 'pattern_name')
    op.drop_column('block', 'pattern_group_id')
    # ### end Alembic commands ###
