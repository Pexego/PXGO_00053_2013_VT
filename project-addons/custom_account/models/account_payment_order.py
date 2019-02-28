# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, _
from odoo.exceptions import UserError


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def generate_payment_file(self):
        self.ensure_one()
        errors = ""
        for line in self.bank_line_ids:
            if not line.mandate_id:
                errors += _("\nMissing SEPA Direct Debit mandate on the "
                            "bank payment line with partner '%s' "
                            "(reference '%s').") % (line.partner_id.name,
                                                    line.name)
            elif line.mandate_id.state != 'valid':
                errors += _("\nThe SEPA Direct Debit mandate with reference "
                            "'%s' for partner '%s' has expired.") % (
                    line.mandate_id.unique_mandate_reference,
                    line.mandate_id.partner_id.name)
            elif line.mandate_id.type == 'oneoff':
                if line.mandate_id.last_debit_date:
                    errors += _("\nThe mandate with reference '%s' for partner"
                                " '%s' has type set to 'One-Off' and it has a "
                                "last debit date set to '%s', so we can't use "
                                "it.") % (
                        line.mandate_id.unique_mandate_reference,
                        line.mandate_id.partner_id.name,
                        line.mandate_id.last_debit_date)
        if errors:
            raise UserError(errors)
        return super().generate_payment_file()
