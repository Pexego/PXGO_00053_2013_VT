# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PaymentOrderLine(models.Model):

    _inherit = 'account.payment.line'

    _order = 'partner_name'

    partner_name = fields.Char(related='partner_id.name', store=True)

    @api.model
    def create(self, vals=None):
        if vals is None:
            vals = {}
        partner_bank_id = vals.get('bank_id')
        move_line_id = vals.get('move_line_id')
        partner_id = vals.get('partner_id')
        if self.env.context.get('search_payment_order_type') == 'debit' and 'mandate_id' not in vals:
            if move_line_id:
                line = self.env['account.move.line'].browse(move_line_id)
                if line.invoice and line.invoice.type == 'out_invoice' and line.invoice.mandate_id:
                    if line.invoice.mandate_id.state == 'valid':
                        vals.update({
                            'mandate_id': line.invoice.mandate_id.id,
                            'bank_id': line.invoice.mandate_id.partner_bank_id.id,
                        })
            if partner_bank_id and 'mandate_id' not in vals:
                mandates = self.env['account.banking.mandate'].search_read(
                    [('partner_bank_id', '=', partner_bank_id),
                     ('state', '=', 'valid')], ['id'])
                if mandates:
                    vals['mandate_id'] = mandates[0]['id']
                else:
                    banking_mandate_valid = self.env['account.banking.mandate'].search_read(
                        [('partner_id', '=', partner_id), ('state', '=', 'valid')],
                        ['id', 'partner_bank_id'])
                    if banking_mandate_valid:
                        vals.update({
                            'mandate_id': banking_mandate_valid[0]['id'],
                            'bank_id': banking_mandate_valid[0]['partner_bank_id'][0],
                        })
        if 'mandate_id' not in vals:
            vals['mandate_id'] = False
        return super(PaymentOrderLine, self).create(vals)


class PaymentOrder(models.Model):

    _inherit = 'account.payment.order'

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
