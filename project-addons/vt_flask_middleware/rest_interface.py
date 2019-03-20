from flask_peewee.rest import RestAPI, RestResource, UserAuthentication

from app import app
from sync_log import SyncLog
from auth import auth
from implemented_models import MODELS_CLASS

user_auth = UserAuthentication(auth, protected_methods=['GET', 'POST', 'PUT',
                                                        'DELETE'])
api = RestAPI(app, default_auth=user_auth)


class ApiResource(RestResource):
    def check_post(self, obj=None):
        return False

    def check_put(self, obj):
        return False

    def check_delete(self, obj):
        return False

for mod_class in list(MODELS_CLASS.keys()):
    api.register(MODELS_CLASS[mod_class], ApiResource)

api.register(SyncLog, ApiResource)

api.setup()
