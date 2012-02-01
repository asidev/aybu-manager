#!/usr/bin/python

import os
from paste.deploy import loadapp
from paste.script.util.logging_config import fileConfig

ini_file = "${instance.paths.pyramid_config}"
fileConfig(ini_file)
os.environ['uWSGI_VHOST_MODE'] = '1'
application = loadapp("config:%s" % (ini_file))
