"""Added relationship between groups and instances

Revision ID: 35360c0a6b47
Revises: c16f3da9876
Create Date: 2012-02-08 17:00:43.792045

"""

# downgrade revision identifier, used by Alembic.
revision = '35360c0a6b47'
down_revision = 'c16f3da9876'

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.alter_column(u'groups', u'name',
                    type_=sa.Unicode(255),
                    existing_server_default=None,
                    existing_nullable=False)
    op.add_column(u'groups', sa.Column('instance_id', sa.Integer(),
                                       nullable=True))
    op.create_foreign_key(u'groups_instance_id_fkey', u'groups',
                          u'instances', ['instance_id'], ['id'],
                          onupdate='CASCADE', ondelete='CASCADE')


def downgrade():
    op.drop_constraint(u'groups_instance_id_fkey', u'groups')
    op.drop_column(u'groups', 'instance_id')
    op.alter_column(u'groups', u'name',
                    type_=sa.Unicode(32),
                    existing_server_default=None,
                    existing_nullable=False)
