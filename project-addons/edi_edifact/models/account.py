from odoo import models, fields, api, exceptions, _
import time
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

