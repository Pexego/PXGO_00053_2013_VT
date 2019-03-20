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

    def __unicode__(self):
        return self.name


class RmaStage(SyncModel):
    MOD_NAME = 'rmastage'

    odoo_id = IntegerField(unique=True)
    name = CharField(max_length=150)

    def __unicode__(self):
        return self.name


class Rma(SyncModel):
    odoo_id = IntegerField(unique=True)
    partner_id = ForeignKeyField(Customer, related_name='rmas',
                                 on_delete='CASCADE')
    stage_id = ForeignKeyField(RmaStage, related_name='rmas',
                               on_delete='CASCADE')
    date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    date_received = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    delivery_type = CharField(max_length=45)
    number = CharField(max_length=45)
    type = CharField(max_length=12)
    last_update_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    delivery_address = CharField(max_length=150)
    delivery_zip = CharField(max_length=15)
    delivery_city = CharField(max_length=45)
    delivery_state = CharField(max_length=45)
    delivery_country = CharField(max_length=150)

    MOD_NAME = 'rma'

    def __unicode__(self):
        return "%s - %s" % (self.odoo_id, self.number)


class RmaProduct(SyncModel):
    odoo_id = IntegerField(unique=True)
    id_rma = ForeignKeyField(Rma, on_delete='CASCADE')
    reference = CharField(max_length=45)
    name = CharField()
    move_out_customer_state = CharField()
    internal_description = CharField()
    product_returned_quantity = FloatField(default=0.0)
    entrance_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'], null=True)
    end_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'], null=True)
    product_id = ForeignKeyField(Product, on_delete='CASCADE', null=True)
    equivalent_product_id = ForeignKeyField(Product, on_delete='CASCADE', null=True, related_name='equivalent_product_set')
    status_id = ForeignKeyField(RmaStatus, on_delete='CASCADE', null=True)
    prodlot_id = CharField(max_length=45)
    invoice_id = CharField(max_length=45)

    MOD_NAME = 'rmaproduct'

    def __unicode__(self):
        return "%s - %s" % (self.reference, self.product_id)
