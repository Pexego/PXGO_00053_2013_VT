# -*- coding: utf-8 -*-
from peewee import CharField, IntegerField, DateTimeField, ForeignKeyField, TextField, BooleanField
from app import app
from customer import Customer
from product import Product
from database import SyncModel


class Picking(SyncModel):
    odoo_id = IntegerField(unique=True)
    name = CharField(unique=True, max_length=150)
    partner_id = ForeignKeyField(Customer, on_delete='CASCADE')
    date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    date_done = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'], null=True)
    move_type = CharField(max_length=15)
    carrier_name = CharField(max_length=50, null=True)
    carrier_tracking_ref = CharField(max_length=150, null=True)
    origin = CharField(max_length=30)
    state = CharField(max_length=30)
    pdf_file_data = TextField()
    dropship = BooleanField(default=False)

    MOD_NAME = 'picking'

    def __unicode__(self):
        return u'%s - %s' % (self.name, self.origin)


class PickingProduct(SyncModel):
    odoo_id = IntegerField(unique=True)
    product_id = ForeignKeyField(Product, on_delete='CASCADE')
    product_qty = IntegerField()
    picking_id = ForeignKeyField(Picking, on_delete='CASCADE')

    MOD_NAME = 'pickingproduct'

    def __unicode__(self):
        return u'%s - %s' % (self.product_id, self.picking_id)