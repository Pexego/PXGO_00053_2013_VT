from odoo import models, api, exceptions, fields, _


class AccountVoucherWizard(models.TransientModel):

    _inherit = "account.voucher.wizard"

    @api.model
    def _get_old_payments(self):
        wiz_lines = []
        order = self.env['sale.order'].browse(self.env.context['active_id'])
        for move in self.env['account.move.line'].search([('payment_id', '!=', False),
                                                          ('partner_id', '=', order.partner_id.id),
                                                          ('amount_residual', '<', 0)]):

            wiz_lines.append({'ref': move.ref,
                              'residual': move.amount_residual,
                              'move_id': move.id,
                              'journal': move.journal_id.name,
                              'sale_order': move.payment_id.sale_id.name,
                              })
        return wiz_lines

    add_old_payments = fields.Boolean(string='Assign old payments')
    old_payment_ids = fields.One2many('old.payment.line', 'wizard_id', default=_get_old_payments)

    @api.constrains('amount_advance')
    def check_amount(self):
        if self.amount_advance <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be "
                                               "positive."))

    @api.onchange('add_old_payments')
    def fill_dummy_data(self):
        if self.add_old_payments:
            self.journal_id = 7
            self.amount_advance = 1.0

    @api.multi
    def make_advance_payment_from_old(self):
        old_pay_line = self.old_payment_ids.filtered(lambda p: p.selected)
        sale_ids = self.env.context.get('active_ids', [])
        payment_obj = self.env['account.payment']
        if len(old_pay_line) == 1 and sale_ids:
            sale = self.env['sale.order'].browse(sale_ids[0])
            old_pay = old_pay_line.move_id.payment_id

            new_pay = {
                'payment_type': 'inbound',
                'partner_id': old_pay.partner_id.id,
                'partner_type': 'customer',
                'journal_id': old_pay.journal_id.id,
                'company_id': old_pay.company_id.id,
                'currency_id': old_pay.currency_id.id,
                'payment_date': old_pay.payment_date,
                'amount': -old_pay_line.residual,
                'sale_id': sale.id,
                'name': _("Advance Payment") + " - " + sale.name,
                'communication': old_pay.communication,
                'payment_reference': old_pay.payment_reference,
                'payment_method_id': self.env.
                    ref('account.account_payment_method_manual_in').id
            }
            payment = payment_obj.create(new_pay)

            moves = self.env['account.move.line'].search([('payment_id', '=', old_pay.id)])
            for move in moves:
                move.old_payment_id = old_pay.id
                move.payment_id = payment.id
            payment.state = "posted"

        else:
            raise exceptions.ValidationError(_("Select just one payment"))

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        sale_ids = self.env.context.get('active_ids', [])
        if not sale_ids:
            return res
        sale_id = sale_ids[0]

        sale = self.env['sale.order'].browse(sale_id)

        total_advance = res['amount_total']
        for payment in sale.account_payment_ids:
            if payment.state == 'cancelled':
                total_advance += payment.amount

            if 'amount_total' in fields:
                res.update({'amount_total': total_advance})

        return res


class OldPaymentLine(models.TransientModel):

    _name = "old.payment.line"

    selected = fields.Boolean()
    wizard_id = fields.Many2one('account.voucher.wizard')
    move_id = fields.Many2one('account.move.line')
    ref = fields.Char('Ref.', related='move_id.ref')
    residual = fields.Monetary('Amount', currency_field='company_currency_id', related='move_id.amount_residual')
    journal = fields.Char('Journal', related='move_id.journal_id.name')
    sale_order = fields.Char('Order', related='move_id.payment_id.sale_id.name')
    company_currency_id = fields.Many2one('res.currency', related='move_id.company_currency_id')
