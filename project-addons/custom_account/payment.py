# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PaymentOrderLine(models.Model):

    _inherit = 'payment.line'

    _order = 'partner_name'

    partner_name = fields.Char(related='partner_id.name', store=True)


class PaymentOrder(models.Model):

    _inherit = 'payment.order'

    @api.multi
    def action_sent(self):
        mail_pool = self.env['mail.mail']
        mail_ids = self.env['mail.mail']
        ctx = {}
        for order in self:
            if order.not_send_emails:
                continue
            partners = {}
            for line in order.line_ids:
                if line.partner_id.email2 or line.partner_id.email:
                    if partners.get(line.partner_id):
                        partners[line.partner_id].append(line)
                    else:
                        partners[line.partner_id] = [line]

            for partner_data in partners:
                template = self.env.ref('account_banking_sepadd_groupby_partner.payment_order_advise_partner', False)
                ctx = dict(self._context)
                ctx.update({
                    'partner_email': partner_data.email,
                    'partner_email2': partner_data.email2,
                    'partner_id': partner_data.id,
                    'partner_name': partner_data.name,
                    'lines': partners[partner_data]
                })
                mail_id = template.with_context(ctx).send_mail(order.id)
                mail_ids += mail_pool.browse(mail_id)

            order.not_send_emails = True
        self = self.with_context(ctx)
        res = super(PaymentOrder, self).action_sent()

        for order in self:
            order.not_send_emails = False

        if mail_ids:
            mail_ids.send()

        return res
