# -*- coding: utf-8 -*-
"""
Invoice model and helper functions.

It will try to automatically create the invoice table and admin user
if they don't exist.
"""

from peewee import CharField, IntegerField, FloatField, ForeignKeyField, TextField, DecimalField

from database import SyncModel
from customer import Customer

class Invoice(SyncModel):
    odoo_id = IntegerField(unique=True)
    number = CharField(max_length=45)
    partner_id = ForeignKeyField(Customer, related_name='invoices',
                                 on_delete='CASCADE')
    client_ref = CharField(max_length=45)
    date_invoice = CharField(max_length=15)
    date_due = CharField(max_length=15)
    state = CharField(max_length=15)
    subtotal_wt_rect = DecimalField(max_digits=2, decimal_places=2, rounding='ROUND_HALF_EVEN')
    total_wt_rect = DecimalField(max_digits=2, decimal_places=2, rounding='ROUND_HALF_EVEN')
    pdf_file_data = TextField()
    payment_mode_id = CharField(max_length=30)

    MOD_NAME = 'invoice'

    def __unicode__(self):
        return u"%s - %s" % (self.odoo_id, self.number)