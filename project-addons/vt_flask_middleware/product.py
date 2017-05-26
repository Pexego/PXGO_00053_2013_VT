# -*- coding: utf-8 -*-
"""
User model and helper functions.

It will try to automatically create the user table and admin user
if they don't exist.
"""

from peewee import CharField, FloatField, IntegerField, ForeignKeyField, BooleanField
from app import app
from database import SyncModel
from country import Country


class ProductCategory(SyncModel):
    odoo_id = IntegerField(unique=True)
    parent_id = IntegerField()
    name = CharField(max_length=150)

    MOD_NAME = 'productcategory'

    def __unicode__(self):
        return self.name


class ProductBrand(SyncModel):
    MOD_NAME = 'productbrand'
    odoo_id = IntegerField(unique=True)
    name = CharField(max_length=150)

    def __unicode__(self):
        return self.name


class ProductBrandCountryRel(SyncModel):
    MOD_NAME = 'productbrandcountryrel'
    odoo_id = IntegerField(unique=True)
    brand_id = ForeignKeyField(ProductBrand, on_delete='CASCADE')
    country_id = ForeignKeyField(Country, on_delete='CASCADE')

    def __unicode__(self):
        return '%s - %s' % (self.brand_id.name, self.country_id.name)


class Product(SyncModel):
    MOD_NAME = 'product'
    name = CharField(max_length=150)
    code = CharField(max_length=50)
    stock = FloatField(default=0.0)
    odoo_id = IntegerField(unique=True)
    uom_name = CharField(max_length=80)
    categ_id = ForeignKeyField(ProductCategory, on_delete='CASCADE')
    brand_id = ForeignKeyField(ProductBrand, on_delete='CASCADE', null=True)
    pvi_1 = FloatField(default=0.0)
    pvi_2 = FloatField(default=0.0)
    pvi_3 = FloatField(default=0.0)
    pvd_1 = FloatField(default=0.0)
    pvd_2 = FloatField(default=0.0)
    pvd_3 = FloatField(default=0.0)
    last_sixty_days_sales = FloatField(default=0.0)
    joking_index = FloatField(default=0.0)
    external_stock = FloatField(default=0.0)
    sale_ok = BooleanField()

    def __unicode__(self):
        return self.name
