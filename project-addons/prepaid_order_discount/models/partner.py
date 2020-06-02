# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.multi
    def prepaid_payment_term(self):
        # Obtener ids de plazo de pago que requieran prepagar (Prepago y Pago inmediato)
        prepaid_ids = []
        prepaid_ids.extend([self.env['account.payment.term'].
                           with_context(lang='en_US').search([('name', 'ilike', 'Prepaid')]).id])
        prepaid_ids.extend([self.env.ref('account.account_payment_term_immediate').id])
        for partner in self:
            # Si el plazo de pago del cliente coincide con alguno de esos ids, devolver True
            return partner.property_payment_term_id.id in prepaid_ids


