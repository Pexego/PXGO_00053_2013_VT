# -*- coding: utf-8 -*-
"""
Main web page controller.
Handles database connections, login, errors and basic routes.
Can be invoqued as a script to run a local server for testing/development.
"""

from flask import *

from app import app
from database import db
from user import User
from auth import auth
from admin import admin
import rest_interface
import xmlrpc_interface
import atexit
import cron
from apscheduler.schedulers.background import BackgroundScheduler
import logging

log = logging.getLogger('apscheduler.executors.default')
log.setLevel(logging.INFO)  # DEBUG

fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
h = logging.StreamHandler()
h.setFormatter(fmt)
log.addHandler(h)


###############################################################################
# Main script body
###############################################################################

if __name__ == "__main__":
    # This code is only executed if the cowlab.py file is directly called from
    # python and not imported from another python file / console.
    scheduler = BackgroundScheduler()
    scheduler.add_job(cron.check_sync_data, 'interval', minutes=1)
    # Explicitly kick off the background thread
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown(wait=False))
    app.run(host="0.0.0.0")
