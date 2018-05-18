from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class PaymentReturn(models.Model):

    _inherit = 'payment.return'

    @api.multi
    def action_confirm(self):
        res = super(PaymentReturn, self).action_confirm()

        reconcile_partial = [line.reconcile_partial_id.id for line in self.move_id.line_id if line.reconcile_partial_id]

        # Mark negative line as no-followup
        for dline in self.line_ids:
            for deb_line in dline.partner_id.unreconciled_aml_ids:
                if (deb_line.debit - deb_line.credit < 0) \
                        and (deb_line.reconcile_partial_id.id in reconcile_partial):
                    deb_line.write({'blocked': True})

        return res
