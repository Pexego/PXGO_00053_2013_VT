# -*- coding: utf-8 -*-
from peewee import CharField, FloatField, IntegerField, ForeignKeyField, DateTimeField
from app import app
from database import BaseModel
from customer import Customer
from product import Product

class Rma(BaseModel):
    odoo_id = IntegerField()
    partner_id = ForeignKeyField(Customer, related_name='rmas')

    def __unicode__(self):
        return u"%s - %s" % (self.odoo_id, self.partner_id)


class RmaProduct(BaseModel):
    odoo_id = IntegerField()
    id_rma = ForeignKeyField(Rma)
    reference = CharField(max_length=45)
    entrance_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    end_date = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    product_id = ForeignKeyField(Product)

    def __unicode__(self):
        return u"%s - %s" % (self.reference, self.product_id)

def init_db():
    if not Rma.table_exists():
        Rma.create_table()
    if not RmaProduct.table_exists():
        RmaProduct.create_table()

init_db()


