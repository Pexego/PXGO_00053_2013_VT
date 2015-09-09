# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _, exceptions

JOURNAL_TYPE_MAP = {
    ('outgoing', 'customer'): ['sale'],
    ('outgoing', 'supplier'): ['purchase_refund'],
    ('outgoing', 'transit'): ['sale', 'purchase_refund'],
    ('incoming', 'supplier'): ['purchase'],
    ('incoming', 'customer'): ['sale_refund'],
    ('incoming', 'transit'): ['purchase', 'sale_refund'],
}


class StockInvoiceOnShippingTests(models.TransientModel):

    @api.model
    def _get_journal_type(self):
        res_ids = self.env.context.get('active_ids', [])
        pick_obj = self.env['stock.picking']
        pickings = pick_obj.browse(res_ids)
        pick = pickings and pickings[0]
        if not pick or not pick.move_lines:
            return 'sale'
        type = pick.picking_type_id.code
        usage = pick.move_lines[0].location_id.usage if type == 'incoming' \
            else pick.move_lines[0].location_dest_id.usage

        return JOURNAL_TYPE_MAP.get((type, usage), ['sale'])[0]

    @api.model
    def _get_journal_ids(self):
        res = []
        test_company_id = self.env.user.company_id.test_company_id
        if not test_company_id:
            pass
        else:
            journal_type = self._get_journal_type()
            journal_ids = self.sudo().env["account.journal"].\
                search([('company_id', '=', test_company_id.id),
                        ('type', '=', journal_type)])
            for journal in journal_ids:
                res.append((journal.id, journal.name))

        return res

    _name = "stock.invoice.onshipping.test"
    _description = "Stock Invoice Onshipping Test"

    journal_id = fields.Selection(_get_journal_ids,
                                  string='Destination Journal',
                                  required=True)
    group = fields.Boolean("Group by partner")
    invoice_date = fields.Date('Invoice Date')

    @api.model
    def view_init(self, fields_list):
        res = super(StockInvoiceOnShippingTests, self).view_init(fields_list)
        pick_obj = self.env['stock.picking']
        count = 0
        active_ids = self.env.context.get('active_ids', [])
        for pick in pick_obj.browse(active_ids):
            if pick.invoice_state != '2binvoiced':
                count += 1
        if len(active_ids) == count:
            raise exceptions.Warning(_('None of these picking lists require '
                                       'invoicing.'))
        return res

    @api.multi
    def open_invoice(self):
        invoice_ids = self.sudo().create_invoice()
        if not invoice_ids:
            raise exceptions.Warning(_('No invoice created!'))

        return True

    @api.multi
    def create_invoice(self):
        context = dict(self.env.context or {})
        picking_pool = self.env['stock.picking']
        pick_ids = self.env.context.get('active_ids', [])
        for pick in picking_pool.browse(pick_ids):
            if not pick.tests:
                raise exceptions.Warning(_("Picking %s is not invoiceable. "
                                           "No tests") % pick.name)
        data = self[0]
        journal2type = {'sale': 'out_invoice', 'purchase': 'in_invoice',
                        'sale_refund': 'out_refund',
                        'purchase_refund': 'in_refund'}
        context['date_inv'] = data.invoice_date
        acc_journal = self.env["account.journal"]
        journal = acc_journal.sudo().browse(int(data.journal_id))
        inv_type = journal2type.get(journal.type) or 'out_invoice'
        context['inv_type'] = inv_type

        pick_ids = picking_pool.sudo().browse(pick_ids)
        res = pick_ids.action_invoice_create(journal_id=int(data.journal_id),
                                             group=data.group,
                                             type=inv_type)
        for invoice in self.env["account.invoice"].sudo().browse(res):
            invoice.company_id = self.env.user.company_id.test_company_id.id
            invoice.fiscal_position = False
            invoice.payment_term = False
            invoice.tax_line = [(6, 0, [])]
            invoice.period_id = False
            invoice.payment_mode_id = False
            invoice.partner_bank_id = False
            invoice.mandate_id = False
            invoice.user_id = False
            accounts = self.env["account.account"].\
                search([('code', 'like', invoice.account_id.code),
                        ('company_id', '=', self.env.user.company_id.
                         test_company_id.id)])
            invoice.partner_id.company_id = False
            invoice.commercial_partner_id.company_id = False

            invoice.account_id = accounts[0].id
            for line in invoice.invoice_line:
                line.invoice_line_tax_id = [(6, 0, [])]
                line.company_id = self.env.user.company_id.test_company_id.id
                line.move_id = False
                if line.product_id:
                    line.product_id.company_id = False
                accounts = self.env["account.account"].\
                search([('code', 'like', line.account_id.code),
                        ('company_id', '=', self.env.user.company_id.
                         test_company_id.id)])
                line.account_id = accounts[0].id

            invoice.button_reset_taxes()
        return res
