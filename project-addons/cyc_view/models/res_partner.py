from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    credit_available = fields.Float("Credit available", default=0.0)

    @api.onchange('insurance_credit_limit')
    def _onchange_insurance_credit_limit(self):
        self.credit_available = max((self.insurance_credit_limit -
                                     (self._origin.insurance_credit_limit - self.credit_available)), 0)

