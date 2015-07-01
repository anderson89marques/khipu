"""add colum data_excessao

Revision ID: 18da4c37880
Revises: 
Create Date: 2015-06-27 01:39:02.206699

"""

# revision identifiers, used by Alembic.
revision = '18da4c37880'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('khipu_exception', sa.Column('data_excecao', sa.Date))


def downgrade():
    op.drop_column('khipu_exception', 'data_excecao')
