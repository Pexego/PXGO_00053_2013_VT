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
    to_sync = BooleanField(default=False)

    def sync_client(self, recurrent=False):
        if not recurrent:
            to_sync_objs = SyncLog.select().where(SyncLog.id != self.id,
                                                  SyncLog.to_sync == True)
            for obj in to_sync_objs:
                resp = obj.sync_client(recurrent=True)
                if resp:
                    obj.sync = True
                    obj.to_sync = False
                    obj.save()
        url = app.config['NOTIFY_URL']
        user = app.config['NOTIFY_USER']
        password = app.config['NOTIFY_PASSWORD']
        signature = app.config['NOTIFY_SIGNATURE']
        data = {'model': self.model, 'operation': self.operation,
                'odoo_id': self.odoo_id,
                'signature': signature}
        resp = requests.post(url, data=json.dumps(data))
        if resp.status_code == 200:
            self.sync = True
            self.save()
            res = True
        else:
            self.to_sync = True
            self.save()
            res = False

        return res

    def launch_sync(self):
        thread.start_new_thread(SyncLog.sync_client, (self,))
