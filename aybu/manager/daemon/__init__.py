#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2010-2012 Asidev s.r.l.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import ConfigParser
import os
import logging
import logging.config
import sys
from . daemon import AybuManagerDaemon


__all__ = ['start', 'AybuManagerDaemon']


def start():
    parser = argparse.ArgumentParser(description='AyBU manager worker')
    parser.add_argument('configfile', metavar='INI',
                       help='ini file for the daemon')
    args = parser.parse_args()
    configfile = os.path.realpath(args.configfile)
    try:
        try:
            configp = ConfigParser.ConfigParser()
            with open(configfile) as f:
                configp.readfp(f)
            config = {k: v for k,v in configp.items('app:aybu-manager')}
            logging.config.fileConfig(configfile)

        except Exception as e:
            parser.error('Cannot read config file {}: {}'\
                         .format(args.configfile, e))

    except Exception as e:
        raise
        parser.error('Error starting daemon: {}'.format(e))

    log = logging.getLogger("{}:start".format(__name__))
    daemon = None
    try:
        daemon = AybuManagerDaemon(config)
        daemon.start()

    except KeyboardInterrupt:
        log.info("Quitting..")
        exit_status = 0

    except:
        log.exception('Error')
        exit_status = 1

    else:
        log.info("Quitting")
        exit_status = 0

    finally:
        if daemon:
            daemon.worker._Thread__stop()
        sys.exit(exit_status)

