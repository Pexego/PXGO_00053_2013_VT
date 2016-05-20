# -*- coding: utf-8 -*-
"""
Database management and base model
using Peewee <https://github.com/coleifer/peewee> as ORM.
Actually we just use Flask-Peewee <https://github.com/coleifer/flask-peewee>.
"""

from app import app
from flask_peewee.db import Database
from datetime import datetime

#
# Database backend (Flask-Peewee).
#
# Note: It gets the database backend and name from the app configuration.
#
database = Database(app)
db = database.database

#
# Base model and models management.
#


class BaseModel(database.Model):
    """Base model for the selected database backend."""
    pass


class SyncModel(database.Model):

    @classmethod
    def create(cls, **query):
        from sync_log import SyncLog
        from implemented_models import MODELS_CLASS
        res = super(SyncModel, cls).create(**query)
        if cls.MOD_NAME in MODELS_CLASS.keys():
            sync_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log = SyncLog.create(odoo_id=query['odoo_id'], model=cls.MOD_NAME,
                                 operation='create', sync_date=sync_date)
            #log.launch_sync()
        return res

    def save(self, force_insert=False, only=None, is_update=False):
        from sync_log import SyncLog
        from implemented_models import MODELS_CLASS
        if is_update and self.MOD_NAME in MODELS_CLASS.keys():
            sync_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log = SyncLog.create(odoo_id=self.odoo_id, model=self.MOD_NAME,
                                 operation='update', sync_date=sync_date)
        res = super(SyncModel, self).save(force_insert, only)
        #if is_update and self.MOD_NAME in MODELS_CLASS.keys():
        #    log.launch_sync()
        return res

    def delete_instance(self, *args, **kwargs):
        from sync_log import SyncLog
        from implemented_models import MODELS_CLASS
        if self.MOD_NAME in MODELS_CLASS.keys():
            sync_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log = SyncLog.create(odoo_id=self.odoo_id, model=self.MOD_NAME,
                                 operation='delete', sync_date=sync_date)
        res = super(SyncModel, self).delete_instance(*args, **kwargs)
        #if self.MOD_NAME in MODELS_CLASS.keys():
        #    log.launch_sync()
        return res

