from odoo import fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    rmp_partner = fields.Many2one('res.partner',domain=[('supplier','=', True)])

