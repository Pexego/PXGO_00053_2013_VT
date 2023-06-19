from odoo import models, fields


class Country(models.Model):
    _inherit = 'res.country'

    new_default_transporter = fields.Many2one('res.partner', 'Default transporter',
                                              domain=[('is_transporter', '=', True)])
