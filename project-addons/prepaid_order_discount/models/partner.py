# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def prepaid_payment_term(self):
        # Obtener ids de plazo de pago que requieran prepagar (Prepago, 1 días, 3 días, 5 días,
        # 7 días y Pago inmediato)
        prepaid_ids = []
        prepaid_terms = self.env['account.payment.term'].with_context(lang='en_US').search(
            [("name", "in", ("1 day","3 days","5 days","7 days","Prepaid"))])
        prepaid_ids.extend(prepaid_terms.ids)
        prepaid_ids.extend([self.env.ref('account.account_payment_term_immediate').id])
        for partner in self:
            # Si el plazo de pago del cliente coincide con alguno de esos ids, devolver True
            return partner.property_payment_term_id.id in prepaid_ids
