from peewee import CharField, IntegerField, DecimalField
from database import SyncModel


class PaymentLine(SyncModel):
    MOD_NAME = 'paymentline'

    odoo_id = IntegerField(unique=True)
    code = CharField(max_length=60)
    date = CharField(max_length=60)
    invoice_id = IntegerField()
    partner_id = IntegerField()
    amount = DecimalField(max_digits=2, decimal_places=2, rounding='ROUND_HALF_EVEN')

    def __unicode__(self):
        return "%s - %s" % (self.code, self.invoice_id)
