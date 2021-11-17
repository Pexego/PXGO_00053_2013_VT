# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class AccountInvoiceReport(models.Model):

    _inherit = 'account.invoice.report'

    amazon_commercial_partner_id = fields.Many2one('res.partner',string="Commercial Partner")

    def _select(self):
        select_str = super()._select()
        select_str += ', sub.amazon_commercial_partner_id as amazon_commercial_partner_id'
        return select_str

    def _sub_select(self):
        select_str = super()._sub_select()
        select_str += ', COALESCE(partner.amazon_parent_id,ai.commercial_partner_id) as amazon_commercial_partner_id'
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += ', COALESCE(partner.amazon_parent_id,ai.commercial_partner_id)'

        return group_by_str


        

