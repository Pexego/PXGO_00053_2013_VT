from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    risk_insurance_anon = fields.Boolean("Anonymous")

    @api.onchange("risk_insurance_anon")
    def _onchange_anon(self):
        if self.risk_insurance_anon:
            anon_limit = self.env['ir.config_parameter'].sudo().get_param('anon.credit.limit')
            self.insurance_credit_limit = anon_limit
        else:
            self.insurance_credit_limit = 0.0

