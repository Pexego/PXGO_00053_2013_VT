# -*- coding: utf-8 -*-
from peewee import CharField, IntegerField, DateTimeField, BooleanField
from app import app
from database import BaseModel
import requests
import json
import thread


class SyncLog(BaseModel):
    odoo_id = IntegerField()
    model = CharField(max_length=50)
    operation = CharField(max_length=50)
    sync_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    sync = BooleanField(default=False)

    def sync_client(self):
        url = app.config['NOTIFY_URL']
        user = app.config['NOTIFY_USER']
        password = app.config['NOTIFY_PASSWORD']
        data = {'model': self.model, 'operation': self.operation,
                'odoo_id': self.odoo_id}
        resp = requests.post(url, data=json.dumps(data), auth=(user, password))
        if resp.status_code == 200:
            from database import db
            db.connect()
            SyncLog.update(sync=True).where(SyncLog.id == self.id).execute()
            db.close()

    def launch_sync(self):
        thread.start_new_thread(SyncLog.sync_client, (self,))
