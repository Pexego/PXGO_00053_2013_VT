# -*- coding: utf-8 -*-
"""
User model and helper functions.

It will try to automatically create the user table and admin user
if they don't exist.
"""

from peewee import CharField, BooleanField
from flask_peewee.auth import BaseUser
from flask_peewee.utils import make_password
from app import app
from database import BaseModel


class User(BaseModel, BaseUser):
    """
    User model.

    Note: follows the 'user model' protocol specified by flask_peewee.auth.Auth
    """
    username = CharField(max_length=30)
    password = CharField(max_length=46)
    active = BooleanField(default=True)
    admin = BooleanField(default=False)

    def __unicode__(self):
        return self.username

#
# Create the table and initial data if needed.
#
def init_db():
    if not User.table_exists():
        User.create_table()
        User.create(username='admin',
                    password=make_password('admin'),
                    admin=True)
init_db()
