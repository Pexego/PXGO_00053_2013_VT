"""
Admin dashboard.
Configures the admin interface.
"""

from flask_peewee.admin import Admin

from app import app
from auth import auth
from user import User
from sync_log import SyncLog
from implemented_models import MODELS_CLASS, MASTER_CLASSES, DEPENDENT_CLASSES
from flask_peewee.utils import make_password

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
    for mod_class in sorted(DEPENDENT_CLASSES.keys()):
        if not MODELS_CLASS[mod_class].table_exists():
            MODELS_CLASS[mod_class].create_table()


init_db()


for mod_class in MODELS_CLASS:
    admin.register(MODELS_CLASS[mod_class])

admin.register(User)

# Enable the admin interface.
admin.setup()
