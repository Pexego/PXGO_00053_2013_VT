from odoo import models, fields, api


class WizardRemovePartnersFromPaymentOrder(models.TransientModel):

    _name = "wzd.remove.partner.payment.order"

    partner_ids = fields.Many2many("res.partner", string="Partners to remove",
                                   required=True,
                                   domain=['|', ('active', '=', True),
                                           ('active', '=', False)])

    @api.multi
    def action_remove_partners(self):
        self.ensure_one()
        order = self.env['account.payment.order'].\
            browse(self.env.context['active_id'])
        lines_to_remove = order.payment_line_ids.\
            filtered(lambda x: x.partner_id in self.partner_ids)
        if lines_to_remove:
            lines_to_remove.unlink()
