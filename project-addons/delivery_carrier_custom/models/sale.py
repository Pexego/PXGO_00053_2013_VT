from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    transporter_id = fields.Many2one('res.partner', 'Transporter',
                                     domain=[('is_transporter', '=', True)])
    delivery_type = fields.Selection([
        ('shipping', 'Shipping'),
        ('carrier', 'Carrier - Customer'),
        ('installations', 'Pickup in installations')],
        'Delivery type', required=True, default='shipping')

    @api.onchange('partner_id')
    def onchange_partner_id_carrier_id(self):
        super().onchange_partner_id_carrier_id()
        if self.partner_id:
            self.transporter_id = self.partner_id.transporter_id.id
            self.delivery_type = self.partner_id.delivery_type

    @api.multi
    @api.onchange('partner_shipping_id')
    def onchange_partner_id_transporter(self):
        transporter_ids = self.env['res.partner'].search([
            ('is_transporter', '=', True),
            ('country_group_id.country_ids', '=', self.partner_shipping_id.country_id.id)
        ])
        if transporter_ids:
            if self.transporter_id not in transporter_ids:
                self.transporter_id = False
            return {'domain': {'transporter_id': [('id', 'in', transporter_ids.ids)]}}
        all_transporters_ids = self.env['res.partner'].search([('is_transporter', '=', True)])
        return {'domain': {'transporter_id': [('id', 'in', all_transporters_ids.ids)]}}

    @api.multi
    @api.onchange('transporter_id')
    def onchange_transporter_id(self):
        carrier_ids = self.transporter_id.carrier_ids.ids
        if self.carrier_id.id not in carrier_ids:
            self.carrier_id = False
        return {'domain': {'carrier_id': [('id', 'in', carrier_ids)]}}
