# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from datetime import date
from dateutil.relativedelta import relativedelta
import odoorpc
from odoo.tools import float_compare


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        if self.order_id.picking_type_id.force_location:
            for move_dict in res:
                move_dict['location_id'] = \
                    self.order_id.picking_type_id.default_location_src_id.id
        return res


class ProrementRule(models.Model):

    _inherit = "procurement.rule"

    def _prepare_purchase_order(self, product_id, product_qty, product_uom,
                                origin, values, partner):
        res = super()._prepare_purchase_order(product_id, product_qty,
                                              product_uom, origin, values,
                                              partner)
        if partner.automatice_purchases:
            res['force_confirm'] = True
            res['date_planned'] = fields.Datetime.now()
        return res


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.depends('amount_to_invoice_es')
    @api.multi
    def _get_to_invoice_diff(self):
        for order in self:
            order.diff_to_invoice = order.amount_to_invoice_es - order.amount_to_invoice_it

    @api.multi
    def _get_amt_to_invoice(self):
        for order in self:
            order.amount_to_invoice_it = round(sum([l.qty_received * l.price_unit for l in order.order_line]), 2)

    force_confirm = fields.Boolean()
    amount_to_invoice_es = fields.Monetary()
    diff_to_invoice = fields.Monetary(compute='_get_to_invoice_diff', store=True)
    es_sale_order = fields.Char('ES Sale')
    amount_to_invoice_it = fields.Monetary('To Invoice', compute='_get_amt_to_invoice', store=False)

    @api.model
    def _check_picking_to_process(self):
        pickings_to_stock = self.env['stock.picking'].search([('picking_type_id', '=',
                                                               self.env.ref('stock.picking_type_in').id),
                                                              ('location_id', '=',
                                                               self.env.ref('automatize_edi_it.stock_location_vendor_deposit').id),
                                                              ('location_dest_id', '=',
                                                               self.env.ref('stock.stock_location_stock').id),
                                                              ('state', 'in',
                                                               ("assigned", "confirmed", "partially_available"))])
        pickings_to_stock._process_picking()

    @api.model
    def _process_purchase_order_automated(self):
        purchases = self.search([('force_confirm', '=', True),
                                 ('order_line', '!=', False),
                                 ('state', '=', 'draft')])
        for order in purchases:
            order.with_context(bypass_override=True).button_confirm()
            action = order.attach_ubl_xml_file_button()
            attachment = self.env['ir.attachment'].browse(action['res_id'])
            output_folder = self.env['base.io.folder'].\
                search([('direction', '=', 'export')], limit=1)
            if not output_folder:
                raise exceptions.UserError(_("Please create an export folder"))
            output_folder.export_file(attachment.datas, attachment.name)
            order.picking_ids._process_picking()
        self._check_picking_to_process()

    picking_type_id = fields.Many2one('stock.picking.type',
                                      default=lambda self:
                                      self.env.ref('automatize_edi_it.picking_type_receive_top_deposit'))

    def _get_qty_to_invoice_es(self, purchase_ref, odoo_es):
        amt_to_invoice = 0.0
        es_sale = None
        order_es_id = odoo_es.env['sale.order'].search([('client_order_ref', '=', purchase_ref), ('partner_id', '=', 245247)])
        if order_es_id:
            order_es = odoo_es.env['sale.order'].browse(order_es_id)
            es_sale = order_es.name
            if order_es.invoice_status == 'to invoice':
                for line in order_es.order_line:
                    amt_to_invoice += line.qty_to_invoice * line.price_unit
        return amt_to_invoice, es_sale

    def cron_check_qty_to_invoice_lx(self, months=1):
        search_date = (date.today() - relativedelta(months=months)).strftime("%Y-%m-%d")
        purchases = self.search([('invoice_status', '=', 'to invoice'),
                                 ('remark', '=', False),
                                 ('date_order', '>=', search_date)])
        orders_not_found = []
        if purchases:
            # get the server
            server = self.env['base.synchro.server'].search([('name', '=', 'Visiotech')])
            # Prepare the connection to the server
            odoo_es = odoorpc.ODOO(server.server_url, port=server.server_port)
            # Login
            odoo_es.login(server.server_db, server.login, server.password)

            for purchase in purchases:
                if purchase.amount_total != purchase.amount_to_invoice_es:
                    purchase.amount_to_invoice_es, purchase.es_sale_order = self._get_qty_to_invoice_es(purchase.name, odoo_es)
                    if not purchase.es_sale_order:
                        orders_not_found.append(purchase.name)

            odoo_es.logout()
            if orders_not_found:
                vals = {
                    'subject': 'Orders not found in Odoo ES',
                    'body_html': '<br>'.join(orders_not_found),
                    'email_to': 'odoo_team@visiotechsecurity.com',
                    'auto_delete': False,
                    'email_from': 'odoo_team@visiotechsecurity.com',
                }
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()

    def cron_automate_invoicing_lx(self, months=2):
        """
        Creates invoices for purchases and for the related sales in Odoo Spain

        Parameters:
        ----------
        months: Int
            Number of months to search purchases
        """
        search_date = (date.today() - relativedelta(months=months)).strftime("%Y-%m-%d")
        picking_type_domain = (self.env.ref('stock.picking_type_in').id,
                               self.env.ref('stock_dropshipping.picking_type_dropship').id)
        purchases = self.search([('invoice_status', '=', 'to invoice'),
                                 ('date_order', '>=', search_date),
                                 ('partner_id', '=', 27),
                                 ('picking_type_id', 'in', picking_type_domain)])
        purchases_filtered = purchases.filtered(
            lambda p: float_compare(p.amount_to_invoice_it, p.amount_to_invoice_es, precision_digits=2) == 0
        )

        if not purchases_filtered:
            return
        odoo_es = self._get_odoo_es()
        try:
            purchases_filtered._create_invoice_on_batch()
            order_es_ids = odoo_es.env['sale.order'].search([
                ('client_order_ref', 'in', purchases_filtered.mapped('name')), ('partner_id', '=', 245247)
            ])
            orders_es = odoo_es.env['sale.order'].browse([])
            orders_es.action_invoice_create_aux(order_es_ids)
            self.env.cr.commit()
            odoo_es.env.commit()
        except Exception as e:
            self.env.cr.rollback()
            raise e
        finally:
            odoo_es.logout()

    def _create_invoice_on_batch(self):
        """
        Creates an invoice with all purchase order lines.
        Every purchase order have to have the same partner_id
        """
        invoices = self.env["account.invoice"]
        invoice = invoices.create({
            "partner_id": self.mapped('partner_id').id,
            "type": "in_invoice",
        })
        invoice._onchange_partner_id()
        for po in self:
            invoice.currency_id = po.currency_id
            invoice.purchase_id = po
            invoice.purchase_order_change()
        invoice.compute_taxes()

    def _get_odoo_es(self):
        """
        Connects with Odoo Spain Server and logs in and returns the
        connection with the server.

        This connection deactivates auto_commit.

        Returns:
        -------
            Odoo Spain server connection
        """
        server = self.env['base.synchro.server'].search([('name', '=', 'Visiotech')])
        # Prepare the connection to the server
        odoo_es = odoorpc.ODOO(server.server_url, port=server.server_port)
        # Login
        odoo_es.login(server.server_db, server.login, server.password)
        odoo_es.config['auto_commit'] = False
        odoo_es.config['timeout'] = 600
        return odoo_es
