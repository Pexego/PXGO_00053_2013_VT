from odoo import models, fields, api


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    no_rappel = fields.Boolean(states={'draft': [('readonly', False)], 'reserve': [('readonly', False)]})

    @api.model
    def create(self, vals):
        if vals.get('order_id'):
            vals['no_rappel'] = self.env['sale.order'].browse(vals['order_id']).no_rappel
        line = super(SaleOrderLine, self).create(vals)
        return line


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    no_rappel = fields.Boolean("W/O Rappel", states={'draft': [('readonly', False)], 'reserve': [('readonly', False)]})

    @api.onchange('no_rappel')
    def onchange_no_rappel(self):
        for line in self.order_line:
            line.no_rappel = self.no_rappel
