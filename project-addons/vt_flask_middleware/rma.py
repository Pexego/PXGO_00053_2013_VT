# -*- coding: utf-8 -*-
from peewee import CharField, FloatField, IntegerField, ForeignKeyField, \
    DateTimeField
from app import app
from database import SyncModel
from customer import Customer
from product import Product


class RmaStatus(SyncModel):
    MOD_NAME = 'rmastatus'

    odoo_id = IntegerField(unique=True)
    name = CharField(max_length=150)


class Rma(SyncModel):
    odoo_id = IntegerField(unique=True)
    partner_id = ForeignKeyField(Customer, related_name='rmas',
                                 on_delete='CASCADE')

    MOD_NAME = 'rma'

    def __unicode__(self):
        return u"%s - %s" % (self.odoo_id, self.partner_id)


class RmaProduct(SyncModel):
    odoo_id = IntegerField(unique=True)
    id_rma = ForeignKeyField(Rma, on_delete='CASCADE')
    reference = CharField(max_length=45)
    entrance_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    end_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    product_id = ForeignKeyField(Product, on_delete='CASCADE', null=True)
    status_id = ForeignKeyField(RmaStatus, on_delete='CASCADE', null=True)

    MOD_NAME = 'rmaproduct'

    def __unicode__(self):
        return u"%s - %s" % (self.reference, self.product_id)
