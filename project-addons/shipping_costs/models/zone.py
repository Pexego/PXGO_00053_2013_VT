from odoo import fields, models


class LocationZone(models.Model):
    """
    Models zones that groups different postal codes in a country given a transporter
    """
    _name = 'location.zone'

    name = fields.Char(string='Name')
    transporter_id = fields.Many2one('transportation.transporter', string='Transporter')
    country_id = fields.Many2one('res.country', string='Country')
    postal_code_ids = fields.One2many('postal.code.range', 'zone_id', string='Postal Codes')


class PostalCodeRange(models.Model):
    """
    Models a range of postal codes. It is related to a location_zone.
    """
    _name = 'postal.code.range'

    first_code = fields.Integer(string='First')
    last_code = fields.Integer(string='Last')
    zone_id = fields.Many2one('location.zone', string='Zone')


class Country(models.Model):
    _inherit = 'res.country'

    location_zone_ids = fields.One2many('location.zone', 'country_id', string='Zone')
