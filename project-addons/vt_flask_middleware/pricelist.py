from peewee import CharField, FloatField, IntegerField, ForeignKeyField, BooleanField, TextField, DateTimeField
from database import SyncModel
from product import Product,ProductBrandGroup

class ProductPricelist(SyncModel):
    MOD_NAME = 'productpricelist'
    odoo_id = IntegerField(unique=True)
    name = CharField()
    brand_group_id = ForeignKeyField(ProductBrandGroup, on_delete='CASCADE', null=True)

    def __unicode__(self):
        return self.name

class ProductPricelistItem(SyncModel):
    MOD_NAME = 'productpricelistitem'
    name = CharField()
    product_id = ForeignKeyField(Product, on_delete='CASCADE')
    pricelist_id = ForeignKeyField(ProductPricelist, on_delete='CASCADE')
    odoo_id = IntegerField(unique=True)
    price = FloatField(default=0.0)


    def __unicode__(self):
        return '%s - %s' % (self.name, self.product_id.name)

