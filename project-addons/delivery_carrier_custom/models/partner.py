from odoo import fields, models, api, exceptions, _


class Partner(models.Model):
    _inherit = 'res.partner'

    carrier_ids = fields.One2many('delivery.carrier', 'partner_id', string='Services')
    new_transporter_id = fields.Many2one('res.partner', 'Transporter', domain=[('is_transporter', '=', True)])
    carrier_id = fields.Many2one('delivery.carrier', 'Transport service')
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
        if self.carrier_id.id not in carrier_ids:
            self.carrier_id = False
        return {'domain': {'carrier_id': [('id', 'in', carrier_ids)]}}

    @api.multi
    @api.onchange('delivery_carrier_type')
    def onchange_delivery_carrier_type(self):
        carrierServ_id = self.env['delivery.carrier'].search([('name', '=', 'Medios Propios')]).ids
        carrierTrans_id = self.env['res.partner'].search([('name', '=', 'Medios Propios')]).ids  # TODO: ¿cambiar a LX?
        installationServ_id = self.env['delivery.carrier'].search([('name', '=', 'Recoge agencia cliente')]).ids
        installationTrans_id = self.env['res.partner'].search(
            [('name', '=', 'Recoge agencia cliente')]).ids  # TODO: ¿Cambiar a LX?
        if self.delivery_carrier_type == 'installations':
            self.carrier_id = carrierServ_id[0]
            self.new_transporter_id = carrierTrans_id[0]

        if self.delivery_carrier_type == 'carrier':
            self.carrier_id = installationServ_id[0]
            self.new_transporter_id = installationTrans_id[0]

        if self.delivery_carrier_type == 'shipping':
            self.carrier_id = self.carrier_id.id
            self.new_transporter_id = self.new_transporter_id.id


class ResPartnerArea(models.Model):

    _inherit = 'res.partner.area'

    transporter_rel_ids = fields.One2many('area.transporter.rel',
                                          'area_id', 'Transporters')

    @api.onchange('transporter_rel_ids')
    def onchange_transporter_rel(self):
        for record in self.transporter_rel_ids:
            if record.ratio_shipping == 0:
                raise exceptions.except_orm(_('Value error'), _('the ratio can not be 0'))

    @api.one
    def write(self, values):
        super().write(values)
        for record in self.transporter_rel_ids:
            if record.ratio_shipping == 0:
                raise exceptions.except_orm(_('Value error'), _('the ratio can not be 0'))
