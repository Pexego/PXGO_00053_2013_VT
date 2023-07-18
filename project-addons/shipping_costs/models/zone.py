from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning
import re


class ShippingZone(models.Model):
    """
    Models zones that groups different postal codes in a country given a transporter
    """
    _name = 'shipping.zone'

    name = fields.Char(string='Name')
    transporter_id = fields.Many2one('res.partner', string='Transporter')
    country_id = fields.Many2one('res.country', string='Country')
    postal_code_ids = fields.One2many('postal.code.range', 'shipping_zone_id', string='Postal Codes')
    shipping_cost_ids = fields.One2many('shipping.cost', 'shipping_zone_id', string='Shipping costs')

    def is_postal_code_in_zone(self, code_to_check):
        """
        Checks if the given postal code is in this zone.
        NOTE: We assume code_to_check fts with postal code's format

        Parameters
        ----------
        code_to_check:
            string with the postal code to check

        Returns
        -------
            If code_to_check in zone postal codes
        """
        for postal_code_range in self.postal_code_ids:
            if postal_code_range.is_postal_code_in_range(code_to_check):
                return True
        return False


class PostalCodeRange(models.Model):
    """
    Models a range of postal codes. It is related to a location_zone.
    """
    _name = 'postal.code.range'

    first_code = fields.Char(string='First', size=10, required=True)
    last_code = fields.Char(string='Last', size=10, required=True)
    shipping_zone_id = fields.Many2one('shipping.zone', string='Zone')
    postal_code_format_id = fields.Many2one(
        str='Postal code format',
        related='shipping_zone_id.country_id.postal_code_format_id'
    )

    def is_postal_code_in_range(self, code_to_check):
        """
        Checks if the given postal code is in this postal_code_range.

        Parameters
        ----------
        code_to_check:
            string with the postal code to check

        Returns
        -------
            If code_to_check in [first_code, last_code]
        """
        return self.first_code <= code_to_check <= self.last_code

    @api.multi
    @api.constrains('first_code', 'last_code')
    def check_postal_codes(self):
        """
        Checks if the range is correctly created:
        - code is a numerical str
        - first_code <= last_code
        """
        for postal_code_range in self:
            if not re.match(postal_code_range.postal_code_format_id.regex, postal_code_range.first_code):
                raise UserError(_(
                    'Not valid postal code value: "%s". Please, try using one like this "%s"') % (
                    postal_code_range.first_code, postal_code_range.postal_code_format_id.postal_code_sample
                ))
            if not re.match(postal_code_range.postal_code_format_id.regex, postal_code_range.last_code):
                raise UserError(_(
                    'Not valid postal code value: "%s". Please, try using one like this "%s"') % (
                    postal_code_range.last_code, postal_code_range.postal_code_format_id.postal_code_sample
                ))
            if postal_code_range.first_code > postal_code_range.last_code:
                raise Warning(_('Error!:: End code is lower than first code.'))


class PostalCodeFormat(models.Model):
    """
    Models the format that a Postal Code must have
    """
    _name = 'postal.code.format'

    name = fields.Char(string='Name')
    country_ids = fields.One2many('res.country', 'postal_code_format_id', string='Country')
    regex = fields.Char(
        string='Regular expression',
        help='With this regular expression you will tell how is the format of the postal code.'
    )
    postal_code_sample = fields.Char(
        string='Code Sample',
        help='An example of how the postal code format must be.'
    )

    @api.multi
    @api.constrains('regex', 'postal_code_sample')
    def check_postal_code_sample(self):
        """
        Checks if the postal_code_sample chosen fits with the regex
        """
        for code_format in self:
            if not re.match(code_format.regex, code_format.postal_code_sample):
                raise UserError(_(
                    'Not valid postal code sample: "%s"') % code_format.postal_code_sample)


class Country(models.Model):
    _inherit = 'res.country'

    shipping_zone_ids = fields.One2many('shipping.zone', 'country_id', string='Zone')
    postal_code_format_id = fields.Many2one(
        'postal.code.format',
        string='Postal Code Format'
    )

