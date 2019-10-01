from peewee import CharField, IntegerField, DateTimeField, BooleanField
from app import app
from database import BaseModel
import requests, requests.utils
import pickle
import json
import hmac
import time
import hashlib


def _get_signature():
    key = r"Z%z^Q%\*v165a"
    key += time.strftime("%d-%m-%y")
    key += r"p2s69\aNz-u}"
    b = bytes(key, encoding='utf8')
    msg = bytes("Hola, soy Odoo", encoding='utf8')
    return hmac.new(b, msg, hashlib.sha256).hexdigest()


class SyncLog(BaseModel):
    odoo_id = IntegerField()
    model = CharField(max_length=50)
    operation = CharField(max_length=50)
    sync_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    sync = BooleanField(default=False)
    to_sync = BooleanField(default=False)

    def sync_client(self):
        url = app.config['NOTIFY_URL']
        header = app.config['NOTIFY_HEADER']
        headers = {'x-api-key': header}

        signature = _get_signature()
        data = {'signature': signature,
                'data': [{'model': self.model,
                          'operation': self.operation,
                          'odoo_id': self.odoo_id}]}
        try:
            print(("DATA: ", data))
            resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=180)
            print(("RESP: ", resp))
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
            res = False
            self.to_sync = True
            self.sync = False
            self.save()
        return res

    def multisync_client(self, objs):
        url = app.config['NOTIFY_URL']
        header = app.config['NOTIFY_HEADER']
        headers = {'x-api-key': header}
        signature = _get_signature()
        to_sync = True
        sync = False
        res = False
        data = {'signature': signature,
                'data': []}
        for record in objs:
            data['data'].append({'model': record.model,
                                 'operation': record.operation,
                                 'odoo_id': record.odoo_id})
        try:
            print(("DATA: ", data))
            cookies_file = open('cookies.data', 'w+b')
            try:
                cookies = requests.utils.cookiejar_from_dict(pickle.load(cookies_file))
            except EOFError:
                cookies = {}
            resp = requests.post(url, headers=headers, data=json.dumps(data),
                                 timeout=6*len(objs), cookies=cookies)
            pickle.dump(requests.utils.dict_from_cookiejar(resp.cookies), cookies_file)
            cookies_file.close()
            print(("RESP: ", resp))
            if resp.status_code == 200:
                sync = True
                to_sync = False
                res = True
        except Exception:
            pass

        for record in objs:
            record.sync = sync
            record.to_sync = to_sync
            record.save()

        return res

    def launch_sync(self):
        #thread.start_new_thread(SyncLog.sync_client, (self,))
        self.sync_client()
