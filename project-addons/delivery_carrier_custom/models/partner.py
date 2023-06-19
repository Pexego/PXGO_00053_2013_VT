from odoo import fields, models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    carrier_ids = fields.One2many('delivery.carrier', 'partner_id', string='Services')
    new_transporter_id = fields.Many2one('res.partner', 'Transporter', domain=[('is_transporter', '=', True)])
    new_service_id = fields.Many2one('delivery.carrier', 'Transport service')
    is_transporter = fields.Boolean('Transporter')
    delivery_carrier_type = fields.Selection([
        ('shipping', 'Shipping'),
        ('carrier', 'Carrier - Customer'),
        ('installations', 'Pickup in installations')],
        'Delivery type', required=True, default='shipping')
    country_group_id = fields.Many2one('res.country.group', 'Country Group')

    @api.multi
    @api.onchange('country_id')
    def new_onchange_country_id(self):
        for partner in self:
            partner.new_transporter_id = partner.country_id.new_default_transporter

    @api.multi
    @api.onchange('new_transporter_id')
    def onchange_new_transporter_id(self):
        carrier_ids = [x.id for x in self.new_transporter_id.carrier_ids]
        if self.new_service_id.id not in carrier_ids:
            self.new_service_id = False
        return {'domain': {'new_service_id': [('id', 'in', carrier_ids)]}}

    @api.multi
    @api.onchange('delivery_type')
    def new_onchange_delivery_type(self):
        # TODO: Falta por migrar
        pass
