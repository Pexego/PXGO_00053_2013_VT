from odoo import fields, models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    expenses_journal = fields.Boolean("Expenses Journal")
