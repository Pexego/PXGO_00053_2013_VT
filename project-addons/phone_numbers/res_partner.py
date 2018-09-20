# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

import phonenumbers

class ResPartner(models.Model):
    _inherit = "res.partner"

    phone_fields = ['phone', 'mobile']

    @api.multi
    def write(self, vals):

        vals_reformated = vals
        if not self.parent_id.id:
            if 'phone' in vals or 'mobile' in vals:
                vals_reformated = self._format_numbers(vals)

        return super(ResPartner, self).write(vals_reformated)

    @api.multi
    def create(self, vals):
        # TODO: mirar lo del is_company, poner and o separar en dos if o algo asi
        vals_reformated = vals
        if not self.parent_id.id and 'is_company' in vals:
            if 'phone' in vals or 'mobile' in vals:
                vals_reformated = self._format_numbers(vals)

        return super(ResPartner, self).create(vals_reformated)

    def _format_numbers(self,vals):

        countrycode = self.country_id.code

        for field in self.phone_fields:
            if field in vals and vals[field]:
                try:
                    res_parse = phonenumbers.parse(vals.get(field), countrycode)
                    vals[field] = phonenumbers.format_number(res_parse, phonenumbers.PhoneNumberFormat.E164)
                except Exception, e:
                    raise Warning(
                    ("Cannot format the phone number '%s' to "
                    "international format. Error: %s")
                    % (vals.get(field), e))

        return vals
