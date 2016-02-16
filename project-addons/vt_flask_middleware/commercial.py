# -*- coding: utf-8 -*-
from peewee import CharField, IntegerField
from app import app
from database import SyncModel


class Commercial(SyncModel):
    odoo_id = IntegerField(unique=True)
    name = CharField(max_length=150)
    email = CharField(max_length=150)

    MOD_NAME = 'commercial'

    def __unicode__(self):
        return '%s - %s' % (self.name, self.email)
