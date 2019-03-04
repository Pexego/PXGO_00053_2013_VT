# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PaymentOrderLine(models.Model):

    _inherit = 'account.payment.line'

    _order = 'partner_name'

    partner_name = fields.Char(related='partner_id.name', store=True)

    @api.model
    def create(self, vals):
        partner_bank_id = vals.get('partner_bank_id')
        move_line_id = vals.get('move_line_id')
        partner_id = vals.get('partner_id')
        order_id = vals.get('order_id')
        if order_id:
            order = self.env['account.payment.order'].browse(order_id)
            if order.payment_method_id.mandate_required and not \
                    vals.get('mandate_id'):
                if move_line_id:
                    line = self.env['account.move.line'].browse(move_line_id)
                    if line.invoice_id and \
                            line.invoice_id.type == 'out_invoice' and \
                            line.invoice_id.mandate_id:
                        if line.invoice_id.mandate_id.state == 'valid':
                            vals.update({
                                'mandate_id': line.invoice_id.mandate_id.id,
                                'partner_bank_id':
                                line.invoice_id.mandate_id.partner_bank_id.id})
                if partner_bank_id and not vals.get('mandate_id'):
                    mandates = self.env['account.banking.mandate'].search_read(
                        [('partner_bank_id', '=', partner_bank_id),
                         ('state', '=', 'valid')], ['id'])
                    if mandates:
                        vals['mandate_id'] = mandates[0]['id']
                    else:
                        banking_mandate_valid = \
                            self.env['account.banking.mandate'].\
                            search_read([('partner_id', '=', partner_id),
                                         ('state', '=', 'valid')],
                                        ['id', 'partner_bank_id'])
                        if banking_mandate_valid:
                            vals.update({
                                'mandate_id': banking_mandate_valid[0]['id'],
                                'partner_bank_id':
                                banking_mandate_valid[0]['partner_bank_id'][0],
                            })
        return super().create(vals)
