__author__ = 'alessio.rocchi'

import atexit
import os
import ConfigParser
from threading import Event
import json

from flask import Flask

import requests

from vcloudlib import vcloudsession
from helper import config_section_map

requests.packages.urllib3.disable_warnings()

# load configuration in memory
Config = ConfigParser.ConfigParser()
file_path = os.path.dirname(os.path.abspath(__file__))
Config.read('{}/config.ini'.format(file_path))
log_format = "%(asctime)s [%(name)-6.8s] [%(threadName)-10.10s] [%(levelname)-7.7s]  %(message)s"
host = config_section_map(Config, "vcloud")["host"]
username = config_section_map(Config, "vcloud")["username"]
password = config_section_map(Config, "vcloud")["password"]
poller_thread = None


class Globals:
    free_ip_lock = False
    used_ips = []
    free_ips = {}
    run_trigger = Event()
    jsonified_data = {}
    app = None
    db = None

    def __init__(self):
        self.vcs = vcloudsession.VCS(host=host, username=username, password=password)
        self.dump_file = '{}/jsonified.dump'.format(file_path)


def create_app():
    _app = Flask(__name__)
    _app.secret_key = 'Cloud.123!'
    _app.debug_log_format = log_format
    db_host = config_section_map(Config, 'db')['hostname']
    db_username = config_section_map(Config, 'db')['username']
    db_password = config_section_map(Config, 'db')['password']
    db = config_section_map(Config, 'db')['db']
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/{}'.format(db_username, db_password, db_host, db)
    _app.config.from_object('app.config.DevelopmentConfig')
    _app.logger.debug('Initializing Flask App.')
    # avoid circular dependency
    from app.models import db
    db.init_app(_app)

    return _app

global_variable = Globals()
global_variable.app = create_app()


def start_poller():
    # if poller is not running, i start it once
    global_variable.app.logger.debug("Starting Poller Daemon...")
    global poller_thread
    if poller_thread is None:
        global_variable.vcs.login()
        from core.Collectors import Poller
        poller_thread = Poller(log_format, global_variable=global_variable)
        poller_thread.start()

# read cached data from disk
try:
    with open(global_variable.dump_file, 'r') as _fh:
        dumped_data = _fh.read()
        global_variable.jsonfied_data = json.loads(dumped_data)
except IOError:
    global_variable.jsonfied_data = {}

from app import views, models, api
