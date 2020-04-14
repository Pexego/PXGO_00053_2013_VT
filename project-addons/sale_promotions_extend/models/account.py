# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _, exceptions


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'


    @api.model
    def create(self,vals):
        import ipdb
        ipdb.set_trace()
        for invoice in self:
            print(invoice)
        return super().create(vals)
