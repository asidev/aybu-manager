"""Change relationship between instances and groups from m2m to m2o

Revision ID: 535ddcd39cad
Revises: 4031597ba686
Create Date: 2012-03-10 10:09:02.058131

"""

# downgrade revision identifier, used by Alembic.
revision = '535ddcd39cad'
down_revision = '4031597ba686'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # create parent_name in groups
    op.add_column(
        u'groups',
        sa.Column(u'parent_name',
                  sa.Unicode(255),
                  sa.ForeignKey(u'groups.name',
                                name=u'groups_parent_name_fkey',
                                onupdate='cascade',
                                ondelete='restrict'),
                  nullable=True,
                  default=None
                 )
    )

    # create instance_groups table
    op.create_table(u'instances_groups',
                    sa.Column(u'instance_domain',
                              sa.Unicode(255),
                              sa.ForeignKey(u'instances.domain',
                                            onupdate="cascade",
                                            ondelete="cascade"),
                              primary_key=True),
                    sa.Column(u'group_name',
                              sa.Unicode(255),
                              sa.ForeignKey(u'groups.name',
                                            onupdate="cascade",
                                            ondelete="cascade"),
                              primary_key=True),
                    mysql_engine=u'InnoDB')

    # populate instances_groups
    connection = op.get_bind()
    connection.execute(
        'INSERT INTO instances_groups (instance_domain, group_name) '
        'SELECT instances.domain, groups.name '
        'FROM instances, groups '
        'WHERE instances.id = groups.instance_id '
    )

    # drop f.key for m2o
    op.drop_constraint(u'groups_instance_id_fkey', u'groups')
    op.drop_column(u'groups', u'instance_id')

    # rename organization to company in users table
    op.alter_column(u'users', u'organization',
                    name=u'company',
                    existing_type=sa.Unicode(128),
                    existing_server_default=None,
                    existing_nullable=True)

    # create organization for users
    op.add_column(
        u'users',
        sa.Column(u'organization_name',
                  sa.Unicode(255),
                  sa.ForeignKey(u'groups.name',
                                name='users_organization_name_fkey',
                                onupdate='cascade',
                                ondelete='restrict'
                  ),
                  nullable=True,
                  default=None
        )
    )


def downgrade():
    # cannot "stash" a M2M in a M2O, no way we can do that
    raise NotImplementedError()
