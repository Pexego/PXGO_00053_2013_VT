"""
Admin dashboard.
Configures the admin interface.
"""

from flask_peewee.admin import Admin

from app import app
from auth import auth
from user import User
from sync_log import SyncLog
from implemented_models import MODELS_CLASS, MASTER_CLASSES, DEPENDENT_CLASSES, SECOND_LEVEL_CLASSES, LAST_CLASSES, FOUR_LEVEL_CLASSES
from flask_peewee.utils import make_password
from flask_peewee.admin import AdminModelConverter,ModelAdmin
from playhouse.postgres_ext import ArrayField
from wtforms import fields as f

#
# Setup the admin interface.
#
admin = Admin(app, auth)
auth.register_admin(admin)

#
# Register the models available in the admin interface.
#


def init_db():
    if not SyncLog.table_exists():
        SyncLog.create_table()
    if not User.table_exists():
        User.create_table()
        User.create(username='admin',
                    password=make_password('admin'),
                    admin=True)
    for mod_class in list(MASTER_CLASSES.keys()):
        if not MODELS_CLASS[mod_class].table_exists():
            MODELS_CLASS[mod_class].create_table()
    for mod_class in list(SECOND_LEVEL_CLASSES.keys()):
        if not MODELS_CLASS[mod_class].table_exists():
            MODELS_CLASS[mod_class].create_table()
    for mod_class in sorted(DEPENDENT_CLASSES.keys()):
        if not MODELS_CLASS[mod_class].table_exists():
            MODELS_CLASS[mod_class].create_table()
    for mod_class in sorted(FOUR_LEVEL_CLASSES.keys()):
        if not MODELS_CLASS[mod_class].table_exists():
            MODELS_CLASS[mod_class].create_table()
    for mod_class in sorted(LAST_CLASSES.keys()):
        if not MODELS_CLASS[mod_class].table_exists():
            MODELS_CLASS[mod_class].create_table()

class AdminModelConverterAdd(AdminModelConverter):
    def __init__(self, *args, **kwargs):
        super(AdminModelConverterAdd, self).__init__(*args, **kwargs)
        self.defaults.update({(ArrayField,f.StringField)})

    def handle_array_field(self, model, field, **kwargs):
        return field.name, self.defaults[ArrayField](**kwargs)
class ArrayModel(ModelAdmin):
    form_converter = AdminModelConverterAdd

init_db()


for mod_class in MODELS_CLASS:
    admin.register(MODELS_CLASS[mod_class], ArrayModel)

admin.register(User)

# Enable the admin interface.
admin.setup()
