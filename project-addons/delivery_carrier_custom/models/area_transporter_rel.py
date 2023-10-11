from odoo import models, fields


class AreaTransporterRel(models.Model):

    _name = 'area.transporter.rel'

    area_id = fields.Many2one('res.partner.area', 'Area')
    transporter_id = fields.Many2one('res.partner', 'Transporter',
                                     domain=[('is_transporter', '=', True)])
    ratio_shipping = fields.Integer('ratio')
