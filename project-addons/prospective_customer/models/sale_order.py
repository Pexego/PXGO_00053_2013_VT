from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.partner_id.prospective:
                order.partner_id.write({'active': True, 'prospective': False})
        super().action_confirm()
