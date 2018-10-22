# -*- coding: utf-8 -*-

from peewee import CharField, IntegerField, FloatField, ForeignKeyField
from database import SyncModel
from customer import Customer


class Rappel(SyncModel):

    odoo_id = IntegerField(unique=True)
    name = CharField(max_length=255)

    MOD_NAME = 'rappel'

    def __unicode__(self):
        return self.name


class RappelCustomerInfo(SyncModel):

    odoo_id = IntegerField(unique=True)
    rappel_id = ForeignKeyField(Rappel, on_delete='CASCADE')
    partner_id = ForeignKeyField(Customer, on_delete='CASCADE')
    date_start = CharField(max_length=15)
    date_end = CharField(max_length=15)
    amount = FloatField(default=0.0)
    amount_est = FloatField(default=0.0)

    MOD_NAME = 'rappelcustomerinfo'

    def __unicode__(self):
        return u"Customer: %s - Rappel: %s" % (self.partner_id, self.rappel_id)


class RappelSection(SyncModel):

    odoo_id = IntegerField(unique=True)
    rappel_id = ForeignKeyField(Rappel)
    percent = FloatField(default=0.0)
    rappel_from = FloatField(default=0.0)
    rappel_until = FloatField(default=0.0)

    MOD_NAME = 'rappelsection'

    def __unicode__(self):
        return u"Rappel: %s - Percentage %s" % (self.rappel_id, self.percent)
