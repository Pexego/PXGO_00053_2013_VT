from odoo import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'

    last_supplier = fields.Many2one('res.partner', string='Last supplier')

    def _select(self):
        select_str = ", p.last_supplier_id as last_supplier"
        return super()._select() + select_str

    def _group_by(self):
        group_by_str = ", p.last_supplier_id"
        return super()._group_by() + group_by_str
