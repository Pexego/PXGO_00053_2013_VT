# -*- coding: utf-8 -*-
"""
Invoice model and helper functions.

It will try to automatically create the invoice table and admin user
if they don't exist.
"""

from peewee import CharField, IntegerField, FloatField, ForeignKeyField, DateField

from database import SyncModel
from customer import Customer

class Invoice(SyncModel):
    odoo_id = IntegerField(unique=True)
    number = CharField(max_length=45)
    partner_id = ForeignKeyField(Customer, related_name='invoices',
                                 on_delete='CASCADE')
    # partner_email_web = CharField(max_length=150)
    client_ref = CharField(max_length=45)
    date_invoice = DateField(formats=['%Y-%m-%d %H:%M:%S'])
    date_due = DateField(formats=['%Y-%m-%d %H:%M:%S'])
    state = CharField(max_length=15)
    subtotal_wt_rect = FloatField()
    total_wt_rect = FloatField()

    MOD_NAME = 'invoice'

    def __unicode__(self):
        return u"%s - %s" % (self.odoo_id, self.number)

