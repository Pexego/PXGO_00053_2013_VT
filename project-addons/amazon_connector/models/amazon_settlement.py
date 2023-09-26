from .amazon_api_request import AmazonAPIRequest
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import re
from dateutil.parser import parse
import logging

_logger = logging.getLogger(__name__)


class AmazonSettlement(models.Model):
    _name = 'amazon.settlement'

    _order = "end_date desc"

    name = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    deposit_date = fields.Date()
    amazon_report_document = fields.Char()
    total_amount = fields.Monetary(currency_field='currency_id')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self._default_company_id())
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        store=True, readonly=True)

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get()

    total_amount_company_currency = fields.Monetary(currency_field='company_currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    line_ids = fields.One2many('amazon.settlement.line', 'settlement_id')

    marketplace_id = fields.Many2one('amazon.marketplace', related="line_ids.marketplace_id")

    move_ids = fields.One2many('account.move', "amazon_settlement_id")
    move_refund_ids = fields.One2many('account.move', "amazon_refund_settlement_id")

    @api.multi
    @api.depends("line_ids", "line_ids.state")
    def _compute_state(self):
        for settlement in self:
            line_states = [x.state == 'reconciled' or x.type not in ['Order', 'Refund'] for x in settlement.line_ids]
            if all(line_states):
                settlement.state = 'done'
            elif any(line_states):
                settlement.state = 'partially_reconciled'
            else:
                settlement.state = 'read'

    state = fields.Selection([('read', 'Read'), ('partially_reconciled', 'Partially Reconciled'), ('done', 'Done')],
                             string='Status', readonly=True, copy=False,
                             index=True, track_visibility='onchange', store=True, compute="_compute_state")

    def cron_reconcile_amazon_invoices(self, created_since=False, force_date=False):
        amazon_time_rate_limit = float(self.env['ir.config_parameter'].sudo().get_param('amazon.time.rate.limit'))
        amazon_api = AmazonAPIRequest(self.env.user.company_id, amazon_time_rate_limit)
        if not created_since:
            created_since = (datetime.utcnow() - timedelta(days=14)).isoformat()
        reports_next_token = True
        while reports_next_token:
            if isinstance(reports_next_token, bool):
                reports_next_token = False
            reports_res = amazon_api.get_reports(report_types=['GET_V2_SETTLEMENT_REPORT_DATA_XML'],
                                                 created_since=created_since,
                                                 page_size=10, next_token=reports_next_token)
            reports_next_token = reports_res.next_token
            reports = reports_res.payload
            for report in reports.get('reports'):
                last_report_document = amazon_api.get_report_document(report.get('reportDocumentId'))
                document = last_report_document.get('document')
                document = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', document)
                root = ET.fromstring(document)
                settlement_data = root.find('./Message/SettlementReport/SettlementData')
                """ <SettlementData>
                        <AmazonSettlementID>12343546718237647</AmazonSettlementID>
                        <TotalAmount currency="EUR">34.37</TotalAmount>
                        <StartDate>2021-04-29T09:43:19+00:00</StartDate>
                        <EndDate>2021-05-13T09:35:05+00:00</EndDate>
                        <DepositDate>2021-05-15T09:35:05+00:00</DepositDate>
                    </SettlementData>"""
                if force_date:
                    date = datetime.strftime(parse(settlement_data[3].text), '%Y-%m-%d')
                    limit_date = datetime.strftime(parse(created_since), '%Y-%m-%d')
                    if date < limit_date:
                        continue
                name = settlement_data[0].text
                if self.env['amazon.settlement'].search([('name', '=', name)]):
                    continue
                vals = {'name': name,
                        'start_date': settlement_data[2].text,
                        'end_date': settlement_data[3].text,
                        'deposit_date': settlement_data[4].text,
                        'amazon_report_document': report.get('reportDocumentId'),
                        'total_amount': float(settlement_data[1].text),
                        'currency_id': self.env['res.currency'].search(
                            [('name', '=', settlement_data[1].attrib.get('currency'))]).id}

                settlement = self.create(vals)

                rate = settlement.currency_id.with_context(date=settlement.deposit_date)._get_conversion_rate(
                    settlement.company_currency_id,
                    settlement.currency_id)
                if rate:
                    settlement.total_amount_company_currency = settlement.total_amount / rate
                else:
                    settlement.total_amount_company_currency = settlement.total_amount
                for order in root.iter('Order'):
                    settlement.parse_order_and_refund(order)
                for refund in root.iter('Refund'):
                    settlement.parse_order_and_refund(refund)
                for transaction in root.iter('OtherTransaction'):
                    if transaction[0].tag == 'AmazonOrderID':
                        line_vals = {'type': transaction.tag,
                                     'amazon_order_name': transaction[0].text,
                                     'amazon_order_id': self.env['amazon.sale.order'].search(
                                         [('name', '=', transaction[0].text)]).id,
                                     'transaction_type': transaction[1].text,
                                     'transaction_name': transaction[2].text,
                                     'posted_date': transaction[3].text,
                                     'currency_id': self.env[
                                         'res.currency'].search(
                                         [('name', '=',
                                           transaction[4].attrib.get(
                                               'currency'))]).id,
                                     'amount': float(transaction[4].text),
                                     'settlement_id': settlement.id}
                    else:
                        if transaction[1].tag == 'ShipmentID':
                            cont = 1
                        elif transaction[1].tag == 'PostedDate':
                            cont = -1
                        else:
                            cont = 0
                        line_vals = {'type': transaction.tag,
                                     'transaction_type': transaction[0].text,
                                     'transaction_name': transaction[cont + 1].text if cont != -1 else False,
                                     'posted_date': transaction[cont + 2].text,
                                     'currency_id': self.env[
                                         'res.currency'].search(
                                         [('name', '=',
                                           transaction[cont + 3].attrib.get(
                                               'currency'))]).id,
                                     'amount': float(transaction[cont + 3].text),
                                     'settlement_id': settlement.id}
                        if cont==1:
                            line_vals.update({'shipment_id':transaction[1].text})
                    line = self.env['amazon.settlement.line'].create(line_vals)
                    for item in transaction.iter('OtherTransactionItem'):
                        self.env['amazon.settlement.item'].create({'sku': item[0].text,
                                                                   'qty': float(item[1].text),
                                                                   'amount': float(item[2].text),
                                                                   'currency_id': self.env[
                                                                       'res.currency'].search(
                                                                       [('name', '=',
                                                                         item[2].attrib.get(
                                                                             'currency'))]).id,
                                                                   'line_id': line.id})
                for advertising_transaction in root.iter('AdvertisingTransactionDetails'):
                    line_vals = {
                        'type': 'AdvertisingTransactionDetails',
                        'settlement_id': settlement.id,
                        'transaction_type': advertising_transaction[0].text,
                        'posted_date': advertising_transaction[1].text,
                        'invoice_name': advertising_transaction[2].text,
                        'base_amount': float(advertising_transaction[3].text),
                        'currency_id': self.env[
                            'res.currency'].search(
                            [('name', '=',
                              advertising_transaction[3].attrib.get(
                                  'currency'))]).id,
                    }
                    if line_vals.get('base_amount') == float(advertising_transaction[4].text):
                        line_vals.update({'amount': float(advertising_transaction[4].text)})
                    else:
                        line_vals.update({'tax_amount': float(advertising_transaction[4].text),
                                          'amount': float(advertising_transaction[5].text)})
                    self.env['amazon.settlement.line'].create(line_vals)
                self.env.cr.commit()
                _logger.info("Reading Settlement %s Done" % name)
                settlement.reconcile()
                lines_error = settlement.line_ids.filtered(
                    lambda l: l.state == 'read' and l.type in ['Order', 'Refund'])
                if lines_error:
                    template = self.env.ref('amazon_connector.send_amazon_settlement')
                    context = {'error_count': len(lines_error),
                               'reconciled_count': len(settlement.line_ids) - len(lines_error),
                               'lang': self.env.user.lang or 'es_ES'}
                    template.with_context(context).send_mail(settlement.id)
                    lines_error.check_other_settlement(settlement)

    def parse_order_and_refund(self, parse_obj, amazon_api=None):
        if not amazon_api:
            amazon_time_rate_limit = float(self.env['ir.config_parameter'].sudo().get_param('amazon.time.rate.limit'))
            amazon_api = AmazonAPIRequest(self.env.user.company_id, amazon_time_rate_limit)
        if parse_obj.tag == 'Order':
            line_type = 'Order'
            item_name = 'Item'
        else:
            line_type = 'Refund'
            item_name = 'AdjustedItem'
        if parse_obj[1].tag == 'MerchantOrderID':
            cont = 2
        else:
            cont = 1
        amazon_order_name = parse_obj[0].text
        line = self.line_ids.filtered(lambda l: l.type == line_type and l.amazon_order_name == amazon_order_name)
        if not line:
            amazon_order = self.env['amazon.sale.order'].search(
                [('name', '=', parse_obj[0].text)])
            line_vals = {'type': line_type,
                         'amazon_order_name': amazon_order_name,
                         'merchant_order_id': parse_obj[1].text if cont == 2 else False,
                         'shipment_id': parse_obj[cont].text if line_type == 'Order' else False,
                         'adjustment_id': parse_obj[cont].text if line_type == 'Refund' else False,
                         'marketplace_id': self.env['amazon.marketplace'].search(
                             [('amazon_name', '=', parse_obj[cont + 1].text)]).id,
                         'fulfillment': parse_obj[cont + 2][0].text,
                         'posted_date': parse_obj[cont + 2][1].text,
                         'settlement_id': self.id}
            if amazon_order:
                line_vals.update({'amazon_order_id': amazon_order.id,
                                  'destination_country_id': amazon_order.country_id.id})
            else:

                order_address = amazon_api.get_order_address(amazon_order_name)
                address = order_address.get('ShippingAddress', False)
                if address.get('CountryCode', False):
                    line_vals.update({'destination_country_id': self.env['res.country'].search(
                        [('code', '=', address.get('CountryCode', False))]).id})

            line = self.env['amazon.settlement.line'].create(line_vals)
        for item_p in parse_obj[cont + 2].iter(item_name):
            item_vals = {'amazon_order_item_code': item_p[0].text,
                         'sku': item_p[1].text if line_type == 'Order' else item_p[2].text,
                         'qty': float(item_p[2].text) if line.type == 'Order' else False,
                         'line_id': line.id}
            item = self.env['amazon.settlement.item'].create(item_vals)
            for item_price in item_p[3]:
                item.parse_item(item_price, 'price')

            if len(item_p) > 4:
                length = 4
                if item_p[4].tag != 'PromotionAdjustment':
                    length += 1
                    for item_fee in item_p[4]:
                        item.parse_item(item_fee, 'fee')

                if len(item_p) > length:
                    for cont in range(length, len(item_p)):
                        item.parse_item(item_p[cont], 'promotion')
        return line

    @api.multi
    def reconcile(self):
        amazon_max_difference_allowed = float(
            self.env['ir.config_parameter'].sudo().get_param('amazon.max.difference.allowed'))
        for settlement in self:
            line_order_ids = settlement.line_ids.filtered(lambda l: l.type == 'Order' and l.state != 'reconciled')
            if line_order_ids:
                settlement._reconcile_amazon_settlement_lines(line_order_ids, amazon_max_difference_allowed)
                lines_error = line_order_ids.filtered(lambda l: l.state != 'reconciled')
                lines_error.check_other_settlement(settlement)
            line_refund_ids = settlement.line_ids.filtered(lambda l: l.type == 'Refund' and l.state != 'reconciled')
            if line_refund_ids:
                settlement._reconcile_amazon_settlement_lines(line_refund_ids, amazon_max_difference_allowed,
                                                              refund_mode=True)

    def _create_move(self, total_amount, total_difference, partner_id, refund_mode=False):
        journal_id = self.env['account.journal'].search([('code', '=', 'AMAZ'), ('name', '=', 'Amazon')])
        vals = {'journal_id': journal_id.id,
                'date': datetime.now()
                }
        if not refund_mode:
            vals.update({'ref': "Pagos desde web Amazon",
                         'amazon_settlement_id': self.id})
        else:
            vals.update({'ref': "Devoluciones desde web Amazon",
                         'amazon_refund_settlement_id': self.id})

        move = self.env['account.move'].create(vals)
        account_430 = self.env['account.account'].search(
            [('code', '=', '43000000'), ('company_id', '=', self.env.user.company_id.id)])
        account_trans = self.marketplace_id.account_id if self.marketplace_id else self.line_ids[
            0].marketplace_id.account_id
        values = {'partner_id': partner_id.id,
                  'journal_id': journal_id.id,
                  'date': datetime.now(),
                  'date_maturity': datetime.now(),
                  'company_id': self.env.user.company_id.id,
                  'move_id': move.id}
        if refund_mode:
            values_430 = {
                'name': "Devoluciones ventas",
                'account_id': account_430.id,
                'debit': total_amount,
            }
            values_trans = {
                'name': "Cobro Amazon",
                'account_id': account_trans.id,
                'credit': total_amount,
            }
        else:
            values_430 = {
                'name': "Ventas no facturadas",
                'account_id': account_430.id,
                'credit': total_amount,
            }

            values_trans = {
                'name': "Pago Amazon",
                'account_id': account_trans.id,
                'debit': total_amount,
            }
        move_lines = []
        if total_difference:
            if total_difference > 0:
                account_difference = self.env['account.account'].search(
                    [('code', '=', '66800001'), ('company_id', '=', self.env.user.company_id.id)])

                values_difference = {'name': "Cambio de divisa", 'account_id': account_difference.id,
                                     'debit': abs(total_difference)}

            else:
                account_difference = self.env['account.account'].search(
                    [('code', '=', '76800001'), ('company_id', '=', self.env.user.company_id.id)])

                values_difference = {'name': "Cambio de divisa", 'account_id': account_difference.id,
                                     'credit': abs(total_difference)}
            if refund_mode:
                values_trans['credit'] = values_trans['credit'] - total_difference
            else:
                values_trans['debit'] = values_trans['debit'] - total_difference
            values_difference.update(values)
            move_lines.append(values_difference)
        values_430.update(values)
        values_trans.update(values)
        move_lines.append(values_trans)
        move_lines.append(values_430)
        move.line_ids = [(0, 0, x) for x in move_lines]
        move.post()
        return move

    def _reconcile_amazon_settlement_lines(self, line_order_ids, amazon_max_difference_allowed, refund_mode=False):
        total_amount = 0
        states = ['cancel']
        moves = {}
        partner_lines = {}
        partner_amount = {}
        partner_difference = {}
        lines_with_moves = self.env['amazon.settlement.line']
        if not refund_mode:
            states += ['paid']
        for line in line_order_ids:
            if not line.amazon_order_id:
                line.amazon_order_id = self.env['amazon.sale.order'].search(
                    [('name', '=', line.amazon_order_name)])
            amazon_invoice = line.amazon_order_id.invoice_deposits.filtered(
                lambda i: i.state not in states and i.type != 'out_refund')
            theoretical_amount = 0
            if amazon_invoice:
                if refund_mode:
                    theoretical_amount +=  line._associate_refunds_to_items()
                else:
                    theoretical_amount = sum(amazon_invoice.mapped('amount_total'))
                rate = line.settlement_id.currency_id.with_context(
                    date=line.posted_date)._get_conversion_rate(
                    line.settlement_id.company_currency_id,
                    line.settlement_id.currency_id)
                positive_events = abs(line.amount_items_positive_events) / rate
                difference = abs(theoretical_amount) - positive_events
                allow_difference = difference <= amazon_max_difference_allowed
                different_currency = line.settlement_id.currency_id != line.settlement_id.company_currency_id
                if allow_difference or different_currency:
                    if line.move_id:
                        lines_with_moves |= line
                        if moves.get(line.move_id, False):
                            moves[line.move_id] |= line
                        else:
                            moves[line.move_id] = line
                    else:
                        invoice_partner = amazon_invoice.partner_id
                        if partner_lines.get(invoice_partner, False):
                            partner_lines[invoice_partner] |= line
                            partner_amount[invoice_partner] += theoretical_amount
                            if different_currency and difference != 0:
                                partner_difference[invoice_partner] += difference
                        else:
                            partner_lines[invoice_partner] = line
                            partner_amount[invoice_partner] = theoretical_amount
                            if different_currency and difference != 0:
                                partner_difference[invoice_partner] = difference
                else:
                    if theoretical_amount > 0:
                        line.error = _('Total amount != Theoretical total amount (%f-%f)\n') % (
                            abs(theoretical_amount), positive_events)
                    theoretical_amount = 0
                if theoretical_amount and not line.move_id:
                    total_amount += theoretical_amount
            else:
                line.error = _('There is no invoice for this order\n')
        if moves:
            for m, lines_to_r in moves.items():
                if refund_mode:
                    lines_to_r.reconcile_refund_lines(m)
                else:
                    lines_to_r.reconcile_order_lines(m)
        for p, lines_group_by_partner in partner_lines.items():
            total_amount = partner_amount.get(p)
            if total_amount > 0:
                total_difference = partner_difference.get(p, False)
                move = self._create_move(total_amount, total_difference, p, refund_mode)
                lines_group_by_partner.write({'move_id': move.id})
                if refund_mode:
                    lines_group_by_partner.reconcile_refund_lines(move)
                else:
                    lines_group_by_partner.reconcile_order_lines(move)

    def action_view_moves(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if len(self.move_ids) > 0:
            action['domain'] = [('id', 'in', self.move_ids.ids)]
            action['context'] = [('id', 'in', self.move_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_refund_moves(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if len(self.move_refund_ids) > 0:
            action['domain'] = [('id', 'in', self.move_refund_ids.ids)]
            action['context'] = [('id', 'in', self.move_refund_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    moves_count = fields.Integer(compute="_compute_moves")
    refund_moves_count = fields.Integer(compute="_compute_moves")

    def _compute_moves(self):
        for settlement in self:
            settlement.moves_count = len(settlement.move_ids)
            settlement.refund_moves_count = len(settlement.move_refund_ids)


class AmazonSettlementLine(models.Model):
    _name = 'amazon.settlement.line'

    type = fields.Selection(
        selection=[('Order', 'Order'),
                   ('Refund', 'Refund'),
                   ('OtherTransaction', 'OtherTransaction'),
                   ('AdvertisingTransactionDetails', 'AdvertisingTransactionDetails')])

    amazon_order_name = fields.Text()
    amazon_order_id = fields.Many2one('amazon.sale.order')
    settlement_id = fields.Many2one('amazon.settlement')
    merchant_order_id = fields.Char()
    shipment_id = fields.Char()
    adjustment_id = fields.Char()
    marketplace_id = fields.Many2one("amazon.marketplace")
    fulfillment = fields.Char()
    posted_date = fields.Date()
    items_ids = fields.One2many("amazon.settlement.item", 'line_id')
    transaction_name = fields.Char()
    transaction_type = fields.Char()
    amount = fields.Monetary('Other Transaction Amount')
    currency_id = fields.Many2one(
        'res.currency',
        readonly=True,
        default=lambda self: self.settlement_id.currency_id.id)
    invoice_name = fields.Char()
    amount_items = fields.Monetary(compute="_compute_items_value")
    amount_items_positive_events = fields.Monetary(compute="_compute_items_positive_items")
    # tax_amount and base_amount only for AdvertisingTransactionDetails type
    tax_amount = fields.Monetary('Advertising Transaction Tax Amount')
    base_amount = fields.Monetary('Advertising Transaction Base Amount')
    state = fields.Selection([('read', 'Read'), ('reconciled', 'Reconciled')], string='Status', readonly=True,
                             copy=False,
                             index=True, track_visibility='onchange', default='read')
    refund_invoice_ids = fields.One2many('account.invoice',compute="_get_refunds")
    refund_state = fields.Selection(related="refund_invoice_id.state")
    error = fields.Char()
    destination_country_id = fields.Many2one('res.country')
    move_id = fields.Many2one('account.move')

    #Fields Deprecated: These fields are only for the old amazon.settlement.line. They are no longer used.
    refund_invoice_id = fields.Many2one('account.invoice')
    refund_amount_untaxed = fields.Monetary(related="refund_invoice_id.amount_untaxed")
    refund_amount_total = fields.Monetary(related="refund_invoice_id.amount_total")

    @api.multi
    def _get_refunds(self):
        for line in self:
            line.refund_invoice_ids = line.items_ids.mapped("refund_id").ids

    @api.multi
    def _compute_items_value(self):
        for line in self:
            amount_items = 0
            if line.type in ['Order', 'Refund']:
                amount_items = sum(line.items_ids.mapped('amount')) + sum(
                    line.items_ids.mapped('item_event_ids.amount'))
            line.amount_items = amount_items

    @api.multi
    def _compute_items_positive_items(self):
        for line in self:
            amount_items_positive_events = 0
            if line.type in ['Order', 'Refund']:
                amount_items_positive_events = sum(
                    line.items_ids.mapped('item_event_ids').filtered(lambda i: i.type != 'fee').mapped('amount'))
            line.amount_items_positive_events = amount_items_positive_events

    @api.multi
    def reconcile_refund_lines(self, move_id):
        max_commit_len = int(self.env['ir.config_parameter'].sudo().get_param('max_commit_len'))
        len_lines = len(self)
        lines_commit = self.env['amazon.settlement.line']
        for count, line in enumerate(self):
            if not line.amazon_order_id:
                am_o = self.env['amazon.sale.order'].search(
                    [('name', '=', line.amazon_order_name)])
                if am_o:
                    line.amazon_order_id = am_o
            if not line.refund_invoice_ids:
                line._associate_refunds_to_items()
            else:
                moves = move_id.line_ids.filtered(
                    lambda ml: ml.account_id.code == '43000000' and ml.debit > 0)
                for refund in line.refund_invoice_ids:
                    move_line_id = refund.move_id.line_ids.filtered(
                        lambda aml: aml.account_id.code == '43000000')
                    if move_line_id:
                        moves += move_line_id
                move_lines_filtered = moves.filtered(lambda aml: not aml.reconciled)
                move_lines_filtered.with_context(skip_full_reconcile_check='amount_currency_excluded').reconcile()
                moves.force_full_reconcile()
                line.state = "reconciled"
            lines_commit += line
            line_number = count + 1
            if (line_number >= max_commit_len and line_number % max_commit_len == 0) or line_number == len_lines:
                self.env.cr.commit()
                _logger.info("COMMIT DONE: %s" % lines_commit)
                lines_commit = self.env['amazon.settlement.line']

    @api.multi
    def _associate_refunds_to_items(self):
        theoretical_amount = 0
        for line in self:
            for item in line.items_ids:
                product = self.env['amazon.sale.order.line'].search(
                    ['&', '|', ('product_seller_sku', '=', item.sku),
                     ('order_item', '=', item.amazon_order_item_code),
                     ('order_id', '=', line.amazon_order_id.id),
                     ]).mapped('product_id')
                if product:
                    refund_sale = line.amazon_order_id.amazon_sale_refund_ids.filtered(
                        lambda il: il.product_id == product[0]
                                   and il.state != 'error' and il.refund_id and il.refund_id.state == 'open')
                    if refund_sale:
                        i_price_unit = refund_sale[0].refund_id.amount_total / (refund_sale[0].product_qty or 1)
                        i_uds = int(abs(sum(
                            item.mapped('item_event_ids').filtered(lambda i: i.type != 'fee').mapped(
                                'amount'))) / i_price_unit)
                        theoretical_amount += i_price_unit * i_uds
                        refund_sale = refund_sale.filtered(lambda r: r.product_qty == i_uds)
                        if refund_sale:
                            item.refund_id = refund_sale[0].refund_id.id
                        else:
                            line.error = _('There is no refund with this qty (%i)\n') %i_uds
                    else:
                        line.error = _('There is no refund invoice for this order\n')
        return theoretical_amount

    @api.multi
    def reconcile_order_lines(self, move_id):
        max_commit_len = int(self.env['ir.config_parameter'].sudo().get_param('max_commit_len'))
        len_lines = len(self)
        lines_commit = self.env['amazon.settlement.line']
        for count, line in enumerate(self):
            if not line.amazon_order_id:
                am_o = self.env['amazon.sale.order'].search(
                    [('name', '=', line.amazon_order_name)])
                if am_o:
                    line.amazon_order_id = am_o
            if line.amazon_order_id:
                move_line_id = self.env['account.move.line'].search(
                    ['&', '|', ('name', 'ilike', line.amazon_order_name),
                     ('invoice_id', 'in',
                      line.amazon_order_id.invoice_deposits.filtered(lambda i: i.state not in ['cancel', 'done']).ids),
                     ('account_id.code', '=', '43000000')])
            else:
                move_line_id = self.env['account.move.line'].search(
                    [('name', 'ilike', line.amazon_order_name), ('account_id.code', '=', '43000000')])
            if move_line_id:
                moves = move_id.line_ids.filtered(
                    lambda ml: ml.account_id.code == '43000000') + move_line_id
                move_lines_filtered = moves.filtered(lambda aml: not aml.reconciled)
                move_lines_filtered.with_context(skip_full_reconcile_check='amount_currency_excluded').reconcile()
                moves.force_full_reconcile()
                line.state = "reconciled"
            lines_commit += line
            line_number = count + 1
            if (line_number >= max_commit_len and line_number % max_commit_len == 0) or line_number == len_lines:
                self.env.cr.commit()
                _logger.info("COMMIT DONE: %s" % lines_commit)
                lines_commit = self.env['amazon.settlement.line']

    @api.multi
    def check_other_settlement(self, settlement):
        amazon_max_difference_allowed = float(
            self.env['ir.config_parameter'].sudo().get_param('amazon.max.difference.allowed'))
        partner_lines ={}
        partner_amount= {}
        partner_difference = {}
        for line in self.filtered(lambda l: l.type == 'Order'):
            equal_lines = self.env['amazon.settlement.line'].search(
                [('amazon_order_name', '=', line.amazon_order_name), ('settlement_id', '!=', line.settlement_id.id),
                 ('type', '=', line.type), ('state', '!=', 'reconciled')])
            if equal_lines:
                amazon_invoice = line.amazon_order_id.invoice_deposits.filtered(
                    lambda i: i.state not in ['cancel', 'done'] and i.type != 'out_refund')
                theoretical_amount = sum(amazon_invoice.mapped('amount_total'))
                rate = line.settlement_id.currency_id.with_context(
                    date=line.amazon_order_id.purchase_date)._get_conversion_rate(
                    line.settlement_id.company_currency_id,
                    line.settlement_id.currency_id)
                positive_events = (abs(line.amount_items_positive_events) + abs(
                    sum(equal_lines.mapped('amount_items_positive_events')))) / rate
                difference = abs(theoretical_amount) - positive_events
                allow_difference = difference <= amazon_max_difference_allowed
                different_currency = line.settlement_id.currency_id != line.settlement_id.company_currency_id
                ls = equal_lines + line
                if allow_difference or different_currency:
                    ls.write({'error': _(
                        'Reconciled with more lines of the same order in other settlements %s') % ls.mapped(
                        'settlement_id.name')})

                    invoice_partner = amazon_invoice.partner_id
                    if partner_lines.get(invoice_partner, False):
                        partner_lines[invoice_partner] |= line
                        partner_amount[invoice_partner] += theoretical_amount
                        if different_currency and difference != 0:
                            partner_difference[invoice_partner] += difference
                    else:
                        partner_lines[invoice_partner] = line
                        partner_amount[invoice_partner] = theoretical_amount
                        if different_currency and difference != 0:
                            partner_difference[invoice_partner] = difference
                else:
                    if theoretical_amount > 0:
                        ls.write({'error': _(
                            'Total amount != Theoretical total amount (%f-%f). (There are more lines in settlement %s)\n') % (
                                               abs(theoretical_amount), positive_events,
                                               ls.mapped('settlement_id.name'))})
                equal_lines.write({'state': "reconciled"})
        for p, lines_group_by_partner in partner_lines.items():
            total_amount = partner_amount.get(p)
            if total_amount > 0:
                total_difference = partner_difference.get(p, False)
                move = settlement._create_move(total_amount, total_difference, p)
                lines_group_by_partner.write({'move_id': move.id})
                lines_group_by_partner.reconcile_order_lines(move)

class AmazonSettlementItem(models.Model):
    _name = 'amazon.settlement.item'

    amazon_order_item_code = fields.Char()
    sku = fields.Char()
    qty = fields.Float()
    line_id = fields.Many2one('amazon.settlement.line')
    item_event_ids = fields.One2many('amazon.settlement.item.event', 'item_id')
    amount = fields.Monetary()
    currency_id = fields.Many2one(
        'res.currency',
        readonly=True,
        default=lambda self: self.line_id.settlement_id.currency_id.id)
    refund_id = fields.Many2one("account.invoice")

    def parse_item(self, event, type):
        name_index = 0 if type != 'promotion' else 1

        self.env['amazon.settlement.item.event'].create(
            {'name': event[name_index].text,
             'type': type,
             'amount': float(event[name_index + 1].text),
             'currency_id': self.env[
                 'res.currency'].search(
                 [('name', '=',
                   event[name_index + 1].attrib.get(
                       'currency'))]).id,
             'item_id': self.id,
             'merchant_promotion': event[
                 0].text if type == 'promotion' else False})


class AmazonSettlementItemEvent(models.Model):
    _name = 'amazon.settlement.item.event'

    name = fields.Char()
    type = fields.Selection([("fee", "Fee"), ("price", "Price"), ("promotion", "Promotion")])
    amount = fields.Monetary()
    item_id = fields.Many2one('amazon.settlement.item')
    currency_id = fields.Many2one(
        'res.currency',
        readonly=True,
        default=lambda self: self.item_id.line_id.settlement_id.currency_id.id)
    merchant_promotion = fields.Char()
