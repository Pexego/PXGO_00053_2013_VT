from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning
import re


class ShippingZone(models.Model):
    """
    Models zones that groups different postal codes in a country given a transporter
    """
    _name = 'shipping.zone'

    name = fields.Char(string='Name')
    transporter_id = fields.Many2one('transportation.transporter', string='Transporter')
    country_id = fields.Many2one('res.country', string='Country')
    postal_code_ids = fields.One2many('postal.code.range', 'shipping_zone_id', string='Postal Codes')
    shipping_cost_ids = fields.One2many('shipping.cost', 'shipping_zone_id', string='Shipping costs')

    def is_postal_code_in_zone(self, code_to_check):
        """
        Checks if the given postal code is in this zone.

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

    first_code = fields.Char(string='First', size=5, required=True)
    last_code = fields.Char(string='Last', size=5, required=True)
    shipping_zone_id = fields.Many2one('shipping.zone', string='Zone')

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
        return self.first_code <= f'{code_to_check:0>5}' <= self.last_code

    @api.model
    def create(self, vals):
        # we complete with zeros on the left until we have 5 characters on postal_codes
        if vals.get('first_code', False):
            vals['first_code'] = f'{vals["first_code"]:0>5}'
        if vals.get('last_code', False):
            vals['last_code'] = f'{vals["last_code"]:0>5}'

        return super().create(vals)

    @api.multi
    def write(self, vals):
        # we complete with zeros on the left until we have 5 characters on postal_codes
        if vals.get('first_code', False):
            vals['first_code'] = f'{vals["first_code"]:0>5}'
        if vals.get('last_code', False):
            vals['last_code'] = f'{vals["last_code"]:0>5}'
        return super().write(vals)

    @api.multi
    @api.constrains('first_code', 'last_code')
    def check_postal_codes(self):
        """
        Checks if the range is correctly created:
        - code is a numerical str
        - first_code <= last_code
        """
        regex = r'\A(\d{1,5})'
        for postal_code_range in self:
            if not re.match(regex, postal_code_range.first_code):
                raise UserError(_(
                    'Not valid postal code value: "%s". Please, use only numbers') % postal_code_range.first_code
                                )
            if not re.match(regex, postal_code_range.last_code):
                raise UserError(_(
                    'Not valid postal code value: "%s". Please, use only numbers') % postal_code_range.last_code
                                )
            if postal_code_range.first_code > postal_code_range.last_code:
                raise Warning(_('Error!:: End code is lower than first code.'))


class Country(models.Model):
    _inherit = 'res.country'

    shipping_zone_ids = fields.One2many('shipping.zone', 'country_id', string='Zone')
