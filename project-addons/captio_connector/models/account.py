from odoo import fields, models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    expenses_journal = fields.Boolean("Expenses Journal")


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    captio_img_url = fields.Char(string="Captio")
