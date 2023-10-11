from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    carrier_ids = fields.One2many('delivery.carrier', 'partner_id', string='Services')
    transporter_id = fields.Many2one('res.partner', 'Transporter', domain=[('is_transporter', '=', True)])
    is_transporter = fields.Boolean('Transporter')
    delivery_type = fields.Selection([
        ('shipping', 'Shipping'),
        ('carrier', 'Carrier - Customer'),
        ('installations', 'Pickup in installations')],
        'Delivery type', required=True, default='shipping')
    country_group_id = fields.Many2one('res.country.group', 'Country Group')

    @api.multi
    @api.onchange('country_id')
    def onchange_country_id(self):
        for partner in self:
            partner.transporter_id = partner.country_id.default_transporter

    @api.multi
    @api.onchange('transporter_id')
    def onchange_transporter_id(self):
        carrier_ids = self.transporter_id.carrier_ids.ids
        if self.property_delivery_carrier_id.id not in carrier_ids:
            self.property_delivery_carrier_id = False
        return {'domain': {'property_delivery_carrier_id': [('id', 'in', carrier_ids)]}}

    @api.multi
    @api.onchange('delivery_type')
    def onchange_delivery_type(self):
        carrier_to_set = False
        transporter_to_set = False

        if self.delivery_type == 'installations':
            carrierServ_id = self.env.ref('delivery_carrier_custom.delivery_carrier_carrier')
            carrier_to_set = carrierServ_id.id
            transporter_to_set = carrierServ_id.partner_id.id

        elif self.delivery_type == 'carrier':
            installationServ_id = self.env.ref('delivery_carrier_custom.delivery_carrier_installations')
            carrier_to_set = installationServ_id.id
            transporter_to_set = installationServ_id.partner_id.id

        elif self.delivery_type == 'shipping':
            carrier_to_set = self.property_delivery_carrier_id.id
            transporter_to_set = self.transporter_id.id

        self.property_delivery_carrier_id = carrier_to_set
        self.transporter_id = transporter_to_set


class ResPartnerArea(models.Model):

    _inherit = 'res.partner.area'

    transporter_rel_ids = fields.One2many('area.transporter.rel',
                                          'area_id', 'Transporters')

    @api.onchange('transporter_rel_ids')
    def onchange_transporter_rel(self):
        for record in self.transporter_rel_ids:
            if record.ratio_shipping == 0:
                raise UserError(_('Value error'), _('the ratio can not be 0'))

    @api.one
    def write(self, values):
        super().write(values)
        for record in self.transporter_rel_ids:
            if record.ratio_shipping == 0:
                raise UserError(_('Value error'), _('the ratio can not be 0'))
