# -*- coding: utf-8 -*-
"""
User model and helper functions.

It will try to automatically create the user table and admin user
if they don't exist.
"""

from peewee import CharField, IntegerField
from app import app
from database import BaseModel


class Customer(BaseModel):
    """
    User model.

    Note: follows the 'user model' protocol specified by flask_peewee.auth.Auth
    """
    fiscal_name = CharField(max_length=150)
    commercial_name = CharField(max_length=150, null=True)
    vat = CharField(max_length=18, null=True)
    street = CharField(max_length=250, null=True)
    city = CharField(max_length=150, null=True)
    zipcode = CharField(max_length=8, null=True)
    country = CharField(max_length=100, null=True)
    state = CharField(max_length=100, null=True)
    email = CharField(max_length=70, null=True)
    odoo_id = IntegerField()

    def __unicode__(self):
        return self.fiscal_name


def init_db():
    if not Customer.table_exists():
        Customer.create_table()

init_db()
