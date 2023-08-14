##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    invoice_type_id = fields.Many2one('res.partner.invoice.type', "Invoice type")

    @api.multi
    def _prepare_invoice(self):
        """ Force the date invoice """
        inv_vals = super()._prepare_invoice()
        force_time = self.env.context.get('force_time')
        if force_time:
            inv_vals['date_invoice'] = force_time
        return inv_vals

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        if self.partner_id:
            part = self.partner_id
            self.invoice_type_id = part.invoice_type_id and part.invoice_type_id.id \
                or part.commercial_partner_id.invoice_type_id and part.commercial_partner_id.invoice_type_id.id \
                or False

    @api.model
    def cron_create_invoices_monthly(self, mode, limit=None):
        """
        Search the orders to invoice and create them grouped by partner
        and commit with every invoice
        :param limit: Limits the number of order to search
        :param mode: The type of invoice, options:
            'Diaria'
            'Mensual'
            'Semanal'
            'Quincenal'
        :returns: true or false
        """
        sale_obj = self.env['sale.order']
        ctx = dict(self._context or {})
        ctx['bypass_risk'] = True
        templates = []
        validate = True
        ok_validation = True

        # Sales to Invoice based on invoicing mode
        sales = sale_obj. \
            search([('invoice_status_2', '=', 'to_invoice'),
                    ('invoice_type_id.name', '=', mode),
                    ('partner_id.no_auto_invoice', '=', False),
                    ('tests', '=', False)],
                   order='confirmation_date desc', limit=limit)

        # Create invoice
        if mode == 'Mensual':
            partners = sales.mapped('partner_id.commercial_partner_id')
            for partner in partners:
                try:
                    sales_to_invoice = sales.filtered(lambda s: s.partner_id == partner and not
                                                                all(s.order_line.filtered(lambda sl: sl.invoice_status == 'to invoice').mapped('deposit')))
                    invoice = sales_to_invoice.action_invoice_create()
                except:
                    print("No invoiceable lines on sale {}".format(sales_to_invoice.mapped('name')))
                    empty_invoices_empty = self.env['account.invoice']. \
                        search([('state', '=', 'draft'),
                                ('origin', '=', ', '.join(sales_to_invoice.mapped('name')))])
                    if empty_invoices_empty:
                        empty_invoices_empty.unlink()
                    invoice = None
                    pass

                invoice_created = self.env['account.invoice'].with_context(ctx).browse(invoice)
                if invoice_created:
                    if len(invoice) != len(invoice_created.mapped('invoice_line_ids.invoice_id.id')):
                        # There are invoices created without lines
                        templates.append(self.env.ref('picking_invoice_pending.alert_cron_create_invoices_empty_lines', False))
                        # Do not validate them because it will generate an error
                        validate = False
                    if validate:
                        # Validate invoice
                        invoice_created.action_invoice_open()
                        if invoice_created.state in ('draft', 'cancel', 'proforma', 'proforma2'):
                            ok_validation = False
                        if not ok_validation:
                            templates.append(self.env.ref('picking_invoice_pending.alert_cron_validate_invoices', False))
                    if invoice_created:
                        for tmpl in templates:
                            ctx.update({
                                'default_model': 'account.invoice',
                                'default_res_id': invoice_created[0].id,
                                'default_use_template': bool(tmpl.id),
                                'default_template_id': tmpl.id,
                                'default_composition_mode': 'comment',
                                'mark_so_as_sent': True
                            })
                            composer_id = self.env['mail.compose.message'].with_context(ctx).create({})
                            composer_id.with_context(ctx).send_mail()
                    self.env.cr.commit()
        return True

    @api.model
    def cron_create_invoices(self, mode, limit=None):
        """
        Search the orders to invoice and create them
        :param limit: Limits the number of order to search
        :param mode: The type of invoice, options:
            'Diaria'
            'Mensual'
            'Semanal'
            'Quincenal'
        :returns: true or false
        """
        sale_obj = self.env['sale.order']
        ctx = dict(self._context or {})
        ctx['bypass_risk'] = True
        templates = []
        validate = True
        ok_validation = True

        # Sales to Invoice based on invoicing mode
        sales = sale_obj.\
            search([('invoice_status_2', '=', 'to_invoice'),
                    ('invoice_type_id.name', '=', mode),
                    ('partner_id.no_auto_invoice', '=', False),
                    ('tests', '=', False)],
                   order='confirmation_date desc', limit=limit)

        # Create invoice
        if mode == 'Diaria':
            invoices = []
            for sale in sales:
                try:
                    invoice = sale.action_invoice_create()
                    invoices.extend(invoice)
                except:
                    print("No invoiceable lines on sale {}".format(sale.name))
                    empty_invoices_empty = self.env['account.invoice']. \
                        search([('state', '=', 'draft'),
                                ('origin', '=', sale.name)])
                    if empty_invoices_empty:
                        empty_invoices_empty.unlink()
                    pass
        elif mode == self.env.ref('custom_partner.biweekly_grouped_by_shipping').name:
            invoices = []
            shipping_addrs = sales.mapped('partner_shipping_id')
            for shipp in shipping_addrs:
                invoice = sales.filtered(lambda s: s.partner_shipping_id == shipp).action_invoice_create()
                invoices.extend(invoice)
        else:
            invoices = sales.action_invoice_create()

        invoices_created = self.env['account.invoice'].with_context(ctx).\
            browse(invoices)
        if len(invoices) != len(invoices_created.mapped('invoice_line_ids.invoice_id.id')):
            # There are invoices created without lines
            templates.append(self.env.ref('picking_invoice_pending.alert_cron_create_invoices_empty_lines', False))
            # Do not validate them because it will generate an error
            validate = False
        if validate:
            # Validate invoice
            for inv in invoices_created:
                inv.action_invoice_open()
                if inv.state in ('draft', 'cancel', 'proforma', 'proforma2'):
                    ok_validation = False
            if not ok_validation:
                templates.append(self.env.ref('picking_invoice_pending.alert_cron_validate_invoices', False))
        if invoices_created:
            for tmpl in templates:
                ctx.update({
                    'default_model': 'account.invoice',
                    'default_res_id': invoices_created[0].id,
                    'default_use_template': bool(tmpl.id),
                    'default_template_id': tmpl.id,
                    'default_composition_mode': 'comment',
                    'mark_so_as_sent': True
                })
                composer_id = self.env['mail.compose.message'].\
                    with_context(ctx).create({})
                composer_id.with_context(ctx).send_mail()

        return True

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final)
        orders_to_done = self.env['sale.order']
        for order in self:
            if not order.order_line.mapped('product_id').filtered(lambda x: x.type != 'service'):
                orders_to_done += order
        orders_to_done.write({'state': 'done'})
        return res

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        invoice_type = (self.invoice_type_id
                        or self.partner_id.commercial_partner_id.invoice_type_id)
        if invoice_type and invoice_type.journal_id:
            res['journal_id'] = invoice_type.journal_id.id
        return res


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    date_order = fields.Datetime(related='order_id.date_order')
    confirmation_date = fields.Datetime(related='order_id.confirmation_date')
