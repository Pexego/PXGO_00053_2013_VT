from odoo import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    last_supplier = fields.Many2one('res.partner', string='Last supplier')

    def _select(self):
        select_str = ', sub.product_last_supplier as last_supplier'
        return super()._select() + select_str

    def _sub_select(self):
        sub_select_str = ', pr.last_supplier_id as product_last_supplier'
        return super()._sub_select() + sub_select_str

    def _group_by(self):
        group_by_str = ', pr.last_supplier_id'
        return super()._group_by() + group_by_str
