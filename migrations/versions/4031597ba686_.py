"""Fixed length for fkey in users_groups

Revision ID: 4031597ba686
Revises: 35360c0a6b47
Create Date: 2012-02-23 10:31:59.812881

"""

# downgrade revision identifier, used by Alembic.
revision = '4031597ba686'
down_revision = '35360c0a6b47'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(u'users_groups', u'groups_name',
                    type_=sa.Unicode(255),
                    existing_server_default=None,
                    existing_nullable=False)


def downgrade():
    op.alter_column(u'users_groups', u'groups_name',
                type_=sa.Unicode(32),
                existing_server_default=None,
                existing_nullable=False)
