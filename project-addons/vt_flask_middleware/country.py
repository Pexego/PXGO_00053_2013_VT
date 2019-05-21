from peewee import CharField, IntegerField, ForeignKeyField
from app import app
from database import SyncModel


class Country(SyncModel):
    odoo_id = IntegerField(unique=True)
    name = CharField(max_length=150)
    code = CharField(max_length=5)

    MOD_NAME = 'country'

    def __unicode__(self):
        return self.name


class CountryState(SyncModel):
    odoo_id = IntegerField(unique=True)
    name = CharField(max_length=150)
    country_id = ForeignKeyField(Country, on_delete='CASCADE')
    code = CharField(max_length=5)

    MOD_NAME = 'countrystate'

    def __unicode__(self):
        return self.name
