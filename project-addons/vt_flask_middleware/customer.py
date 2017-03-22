# -*- coding: utf-8 -*-
"""
User model and helper functions.

It will try to automatically create the user table and admin user
if they don't exist.
"""

from peewee import CharField, IntegerField, FloatField, ForeignKeyField
from commercial import Commercial
from app import app
from database import SyncModel


class Customer(SyncModel):
    """
    User model.

    Note: follows the 'user model' protocol specified by flask_peewee.auth.Auth
    """
    fiscal_name = CharField(max_length=150)
    commercial_name = CharField(max_length=150, null=True)
    pricelist_name = CharField(max_length=150, null=True)
    ref = CharField(max_length=150, null=True)
    discount = FloatField(default=0.0)
    vat = CharField(max_length=18, null=True)
    street = CharField(max_length=250, null=True)
    city = CharField(max_length=150, null=True)
    zipcode = CharField(max_length=8, null=True)
    country = CharField(max_length=100, null=True)
    state = CharField(max_length=100, null=True)
    email = CharField(max_length=70, null=True)
    commercial_id = ForeignKeyField(Commercial, on_delete='CASCADE', null=True)
    odoo_id = IntegerField(unique=True)
    lang = CharField(max_length=5, null=True)

    MOD_NAME = 'customer'

    def __unicode__(self):
        return self.fiscal_name
