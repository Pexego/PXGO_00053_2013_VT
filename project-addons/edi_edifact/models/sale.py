from odoo import models, api, fields, exceptions, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    partner_final_invoicing_id = fields.Many2one('res.partner')

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        inv_vals = super()._prepare_invoice()
        inv_vals['partner_final_invoicing_id'] = self.partner_final_invoicing_id.id
        return inv_vals
