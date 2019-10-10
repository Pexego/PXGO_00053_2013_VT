# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, _
from odoo.exceptions import UserError


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def action_done_cancel(self):
        move_lines = []
        for bline in self.bank_line_ids:
            move_lines = bline.payment_line_ids.mapped('move_line_id')
        res = super().action_done_cancel()
        if move_lines:
            move_lines.remove_move_reconcile()
        return res

    @api.multi
    def draft2open(self):
        for order in self:
            group_paylines = {}
            incorrect_partners = []
            for payline in order.payment_line_ids:
                if order.payment_mode_id.group_lines:
                    hashcode = payline.payment_line_hashcode()
                else:
                    # Use line ID as hascode, which actually means no grouping
                    hashcode = payline.id
                if hashcode in group_paylines:
                    group_paylines[hashcode]['paylines'] += payline
                    group_paylines[hashcode]['total'] +=\
                        payline.amount_currency
                else:
                    group_paylines[hashcode] = {
                        'paylines': payline,
                        'total': payline.amount_currency,
                    }
            for paydict in list(group_paylines.values()):
                # Block if a bank payment line is <= 0
                if paydict['total'] <= 0:
                    incorrect_partners.\
                        append(paydict['paylines'][0].partner_id.id)
            if incorrect_partners:
                incorrect_partners = list(set(incorrect_partners))
                wzd = self.env['wzd.remove.partner.payment.order'].\
                    create({'partner_ids': [(6, 0, incorrect_partners)]})
                result = self.env['ir.actions.act_window'].\
                    for_xml_id('custom_account',
                               'action_wzd_remove_partner_payment_order')
                result['res_id'] = wzd.id
                result['target'] = 'new'
                return result
        return super().draft2open()

    @api.multi
    def generate_payment_file(self):
        self.ensure_one()
        errors = ""
        if self.payment_mode_id.payment_method_id.mandate_required:
            for line in self.bank_line_ids:
                if not line.mandate_id:
                    errors += _("\nMissing SEPA Direct Debit mandate on the"
                                " bank payment line with partner '%s' "
                                "(reference '%s').") % (line.partner_id.name,
                                                        line.name)
                elif line.mandate_id.state != 'valid':
                    errors += _("\nThe SEPA Direct Debit mandate with "
                                "reference '%s' for partner '%s' has "
                                "expired.") % (
                        line.mandate_id.unique_mandate_reference,
                        line.mandate_id.partner_id.name)
                elif line.mandate_id.type == 'oneoff':
                    if line.mandate_id.last_debit_date:
                        errors += _("\nThe mandate with reference '%s' for "
                                    "partner '%s' has type set to 'One-Off' "
                                    "and it has a last debit date set to "
                                    "'%s', so we can't use it.") % (
                            line.mandate_id.unique_mandate_reference,
                            line.mandate_id.partner_id.name,
                            line.mandate_id.last_debit_date)
        if errors:
            raise UserError(errors)
        return super().generate_payment_file()

    @api.multi
    def send_mail(self):
        mail_pool = self.env['mail.mail']
        mail_ids = self.env['mail.mail']
        for order in self:
            if order.not_send_emails:
                continue

            for line in order.bank_line_ids:
                if order.payment_type == 'inbound':
                    template = self.env.ref(
                        'account_banking_sepa_mail.payment_order_advise_partner',
                        False)
                if order.payment_type == 'outbound':
                    template = self.env.ref(
                        'account_banking_sepa_mail.payment_order_advise_supplier',
                        False)
                ctx = dict(self._context)
                ctx.update({
                    'partner_id': line.partner_id.id,
                    'partner_email': line.partner_id.email,
                    # we add the email2, means the accounting email to use it later on the template
                    'partner_email2': line.partner_id.email2,
                    'partner_name': line.partner_id.name,
                    'partner_team': line.partner_id.team_id,
                    'obj': line
                })
                mail_id = template.with_context(ctx).send_mail(order.id)
                mail_ids += mail_pool.browse(mail_id)
            order.not_send_emails = True
            super().send_mail()
            order.not_send_emails = False

        if mail_ids:
            mail_ids.send()

    @api.onchange('payment_mode_id')
    def payment_mode_id_change(self):
        res = super().payment_mode_id_change()
        self.not_send_emails = self.payment_mode_id.not_send_emails
        return res
