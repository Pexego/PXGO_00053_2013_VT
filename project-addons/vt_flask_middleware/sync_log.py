# -*- coding: utf-8 -*-
from peewee import CharField, IntegerField, DateTimeField, BooleanField
from app import app
from database import BaseModel
import requests
import json
import thread
import hmac
import time
import hashlib
 
def _get_signature():
        key = r"Z%z^Q%\*v165a"
        key += time.strftime("%d-%m-%y")
        key += r"p2s69\aNz-u}"
        b = bytes(key)
        return hmac.new(b, "Hola, soy Odoo", hashlib.sha256).hexdigest()


class SyncLog(BaseModel):
    odoo_id = IntegerField()
    model = CharField(max_length=50)
    operation = CharField(max_length=50)
    sync_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    sync = BooleanField(default=False)
    to_sync = BooleanField(default=False)

    def sync_client(self, recurrent=False):
        #if not recurrent:
            #to_sync_objs = SyncLog.select().where(SyncLog.id != self.id,
            #                                      SyncLog.to_sync == True)
            #for obj in to_sync_objs:
            #    resp = obj.sync_client(recurrent=True)
                #if resp:
                #    obj.sync = True
                #    print "SYNC"
                #    obj.to_sync = False
                #    obj.save()
        url = app.config['NOTIFY_URL']
        user = app.config['NOTIFY_USER']
        password = app.config['NOTIFY_PASSWORD']
        signature = _get_signature() 
        data = {'model': self.model, 'operation': self.operation,
                'odoo_id': self.odoo_id,
                'signature': signature}
        try:
            resp = requests.post(url, data=json.dumps(data), timeout=2)
            if resp.status_code == 200:
                self.sync = True
                self.to_sync = False
                self.save()
                res = True
            else:
                self.to_sync = True
                self.sync = False
                self.save()
                res = False
        except Exception:
            res=False
            self.to_sync = True
            self.sync = False
            self.save()
        return res

    def launch_sync(self):
        #thread.start_new_thread(SyncLog.sync_client, (self,))
        self.sync_client()
