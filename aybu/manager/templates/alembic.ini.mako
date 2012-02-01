[alembic]
sqlalchemy.url = ${instance.database_config.sqlalchemy_url}
sqlalchemy.echo = false
script_location = ${instance.environment.paths.migrations}