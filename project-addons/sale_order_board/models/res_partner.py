from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    weight_volume_translation = fields.Float(string="Translation (kg/cbm)")

    country_group_id = fields.Many2one('res.country.group', 'Country Group')

    fuel = fields.Float(string="Fuel(%)",
                        help="Percentage increase in transportation which varies depending on transporter")

    api_name = fields.Char("API Name")
