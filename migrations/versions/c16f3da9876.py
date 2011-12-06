"""empty message

Revision ID: c16f3da9876
Revises: None
Create Date: 2011-12-06 14:35:51.857314

"""

# downgrade revision identifier, used by Alembic.
down_revision = None

from alembic import op
import sqlalchemy as sa
from aybu.manager.models.types import Crypt


def upgrade():

    op.create_table(u'users',
        sa.Column('email', sa.Unicode(length=255), nullable=False),
        sa.Column('password', Crypt(), nullable=False),
        sa.Column('name', sa.Unicode(length=128), nullable=False),
        sa.Column('surname', sa.Unicode(length=128), nullable=False),
        sa.Column('organization', sa.Unicode(length=128), nullable=True),
        sa.Column('web', sa.Unicode(length=128), nullable=True),
        sa.Column('twitter', sa.Unicode(length=128), nullable=True),
        sa.PrimaryKeyConstraint('email')
    )

    op.create_table(u'groups',
        sa.Column('name', sa.Unicode(length=32), nullable=False),
        sa.PrimaryKeyConstraint('name')
    )

    op.create_table(u'users_groups',
        sa.Column('users_email', sa.Unicode(length=255), nullable=True),
        sa.Column('groups_name', sa.Unicode(length=32), nullable=True),
        sa.ForeignKeyConstraint(['groups_name'], ['groups.name'], ),
        sa.ForeignKeyConstraint(['users_email'], ['users.email'], ),
        sa.PrimaryKeyConstraint()
    )

    op.create_table(u'environments',
        sa.Column('name', sa.Unicode(length=64), nullable=False),
        sa.Column('venv_name', sa.Unicode(length=64), nullable=True),
        sa.PrimaryKeyConstraint('name')
    )

    themes_primary = sa.Column('name', sa.Unicode(length=128), nullable=False)
    op.create_table(u'themes',
        themes_primary,
        sa.Column('parent_name', sa.Unicode(length=128), nullable=True),
        sa.Column('version', sa.Unicode(length=16), nullable=True),
        sa.Column('author_email', sa.Unicode(length=255), nullable=True),
        sa.Column('owner_email', sa.Unicode(length=255), nullable=False),
        sa.Column('banner_width', sa.Integer(), nullable=False),
        sa.Column('banner_height', sa.Integer(), nullable=False),
        sa.Column('logo_width', sa.Integer(), nullable=False),
        sa.Column('logo_height', sa.Integer(), nullable=False),
        sa.Column('main_menu_levels', sa.Integer(), nullable=False),
        sa.Column('template_levels', sa.Integer(), nullable=False),
        sa.Column('image_full_size', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('name'),
        sa.ForeignKeyConstraint(['author_email'], ['users.email'], ),
        sa.ForeignKeyConstraint(['owner_email'], ['users.email'], ),
        sa.ForeignKeyConstraint(['parent_name'], [themes_primary], ),
    )

    op.create_table(u'instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.Unicode(length=255), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('owner_email', sa.Unicode(length=255), nullable=False),
        sa.Column('environment_name', sa.Unicode(length=64), nullable=False),
        sa.Column('theme_name', sa.Unicode(length=128), nullable=True),
        sa.Column('technical_contact_email', sa.Unicode(length=255), nullable=False),
        sa.Column('default_language', sa.Unicode(length=2), nullable=True),
        sa.Column('database_password', sa.Unicode(length=32), nullable=True),
        sa.UniqueConstraint('domain'),
        sa.ForeignKeyConstraint(['environment_name'], ['environments.name'], ),
        sa.ForeignKeyConstraint(['owner_email'], ['users.email'], ),
        sa.ForeignKeyConstraint(['technical_contact_email'], ['users.email'], ),
        sa.ForeignKeyConstraint(['theme_name'], ['themes.name'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(u'redirects',
        sa.Column('source', sa.Unicode(length=256), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('target_path', sa.Unicode(length=256), nullable=True),
        sa.Column('http_code', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id'], ),
        sa.PrimaryKeyConstraint('source')
    )

def downgrade():
    op.drop_table(u'redirects')
    op.drop_table(u'users_groups')
    op.drop_table(u'groups')
    op.drop_table(u'instances')
    op.drop_table(u'themes')
    op.drop_table(u'users')
    op.drop_table(u'environments')
