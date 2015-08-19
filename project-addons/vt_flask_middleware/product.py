# -*- coding: utf-8 -*-
"""
User model and helper functions.

It will try to automatically create the user table and admin user
if they don't exist.
"""

from peewee import CharField, FloatField, IntegerField
from app import app
from database import BaseModel


class Product(BaseModel):
    name = CharField(max_length=150)
    code = CharField(max_length=20)
    stock = FloatField(default=0.0)
    odoo_id = IntegerField()
    price_unit = FloatField(default=0.0)
    uom_name = CharField(max_length=80)

    def __unicode__(self):
        return self.name

def init_db():
    if not Product.table_exists():
        Product.create_table()

init_db()
