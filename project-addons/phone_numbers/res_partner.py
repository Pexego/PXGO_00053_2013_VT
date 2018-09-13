# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

import phonenumbers

class ResPartner(models.Model):
    _inherit = "res.partner"

    _phone_fields = ['phone','mobile']

    @api.multi
    def write(self, vals):

        vals_reformated = vals
        if 'phone' in vals or 'mobile' in vals:
            vals_reformated = self._format_numbers(vals)

        return super(ResPartner, self).write(vals_reformated)

    @api.multi
    def create(self, vals):

        vals_reformated = vals
        if 'phone' in vals or 'mobile' in vals:
            vals_reformated = self._format_numbers(vals)

        return super(ResPartner, self).create(vals_reformated)

    def _format_numbers(self,vals):

        import ipdb
        ipdb.set_trace()

        countrycode = self.country_id.code

        for field in self._phone_fields:
            if field in vals:
                try:
                    res_parse = phonenumbers.parse(vals.get(field), countrycode)
                    vals[field] = phonenumbers.format_number(res_parse, phonenumbers.PhoneNumberFormat.E164)
                except Exception, e:
                    raise Warning(
                    ("Cannot reformat the phone number '%s' to "
                    "international format. Error message: %s")
                    % (vals.get(field), e))

        return vals
