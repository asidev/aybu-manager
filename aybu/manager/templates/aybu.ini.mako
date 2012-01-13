[app:aybu-controlpanel]
use = egg:aybu-controlpanel

debug_authorization = false
debug_notfound = false
debug_routematch = false
debug_templates = false
reload_templates = false
reload_assets = false
debug = false

sqlalchemy.url = ${instance.database_config.sqlalchemy_url}
sqlalchemy.echo = false

# session
session.type = file
session.data_dir = ${instance.paths.session.data_dir}
session.lock_dir = ${instance.paths.session.lock_dir}
session.key = ${instance.session_config.key}
session.secret = ${instance.session_config.secret}
session.cookie_on_exception = false

# instance
instance = ${instance.python_name}

# data
default_data = ${instance.paths.data.default}
default_locale_name = ${instance.default_language}

# pyramid_mailer
mail.host = ${smtp.host}
mail.port = ${smtp.port}

# templating
mako.strict_undefined = true
mako.module_directory = ${instance.paths.mako_tmp_dir}

[pshell]
setup = aybu.core.utils.pshell.setup

[pipeline:main]
pipeline =
    aybu-controlpanel

[server:main]
use = egg:Paste#http
host = 0.0.0.0
port = 6543

[loggers]
keys = root, aybu, exc_logger, pufferfish

[handlers]
keys = file, exc_handler, console

[formatters]
keys = generic, exc_formatter

[logger_root]
level = WARN
handlers = file

[logger_aybu]
level = WARN
handlers =
qualname = aybu

[logger_pufferfish]
level = WARN
handlers =
qualname = pufferfish

[logger_exc_logger]
level = ERROR
handlers = exc_handler
qualname = exc_logger

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[handler_file]
class = handlers.RotatingFileHandler
level = NOTSET
formatter = generic
args = ('${instance.paths.logs.application}', 'a', 10485760, 10)

[handler_exc_handler]
class = handlers.SMTPHandler
args = (('${smtp.host}', ${smtp.port}), 'exc@${instance.domain}', ['${instance.technical_contact_email}'], '${instance.domain} Exception')
level = ERROR
formatter = exc_formatter

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s

[formatter_exc_formatter]
format = %(asctime)s %(message)s
