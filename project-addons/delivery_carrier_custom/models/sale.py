from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    new_transporter_id = fields.Many2one('res.partner', 'Transporter',
                                         domain=[('is_transporter', '=', True)])
    delivery_carrier_type = fields.Selection([
        ('shipping', 'Shipping'),
        ('carrier', 'Carrier - Customer'),
        ('installations', 'Pickup in installations')],
        'Delivery type', required=True, default='shipping')

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        if self.partner_id:
            self.new_transporter_id = self.partner_id.new_transporter_id.id
            self.carrier_id = self.partner_id.carrier_id.id
            self.delivery_carrier_type = self.partner_id.delivery_carrier_type

    @api.multi
    @api.onchange('partner_shipping_id')
    def new_onchange_partner_id_transporter(self):
        transporter_ids = self.env['res.partner'].search([
            ('is_transporter', '=', True),
            ('country_group_id.country_ids', 'in', [self.partner_shipping_id.country_id.id])
        ])
        if transporter_ids:
            if self.new_transporter_id not in transporter_ids:
                self.new_transporter_id = False
            return {'domain': {'new_transporter_id': [('id', 'in', transporter_ids.mapped("id"))]}}
        all_transporters_ids = self.env['res.partner'].search([('is_transporter', '=', True)])
        return {'domain': {'new_transporter_id': [('id', 'in', all_transporters_ids.mapped("id"))]}}

    @api.multi
    @api.onchange('new_transporter_id')
    def onchange_new_transporter_id(self):
        carrier_ids = [x.id for x in self.new_transporter_id.carrier_ids]
        if carrier_ids:
            if self.carrier_id.id not in carrier_ids:
                self.carrier_id = False
            return {'domain': {'carrier_id': [('id', 'in', carrier_ids)]}}
        all_carriers = [x.id for x in self.env['delivery.carrier'].search([])]
        return {'domain': {'carrier_id': [('id', 'in', all_carriers)]}}
