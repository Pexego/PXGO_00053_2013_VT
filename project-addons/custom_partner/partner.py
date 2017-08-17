# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pcomunitea.com>$
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

from openerp import models, fields, api, exceptions, osv, _
from openerp.addons.account_followup.report import account_followup_print
from openerp.osv import osv, fields as fields2
from collections import defaultdict
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import dateutil.relativedelta
from openerp.exceptions import ValidationError


class ResPartnerInvoiceType(models.Model):
    _name = 'res.partner.invoice.type'

    name = fields.Char('Name', required=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _purchase_invoice_count(self, cr, uid, ids, field_name, arg, context=None):
        invoice = self.pool.get('account.invoice')
        res = {}
        for partner_id in ids:
            res[partner_id] = invoice.search_count(cr, uid, [
                ('partner_id', 'child_of', partner_id),
                '|', ('type', '=', 'in_invoice'), ('type', '=', 'in_refund')], context=context)
        return res

    def _invoice_total_real(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        if context is None:
            context = {}
        account_invoice_report = self.pool.get('account.invoice.report')
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        user_currency_id = user.company_id.currency_id.id
        for partner_id in ids:
            all_partner_ids = self.pool['res.partner'].search(
                cr, uid, [('id', 'child_of', partner_id)], context=context)

            # searching account.invoice.report via the orm is comparatively expensive
            # (generates queries "id in []" forcing to build the full table).
            # In simple cases where all invoices are in the same currency than the user's company
            # access directly these elements
            domain = [('partner_id', 'in', all_partner_ids),
                      ('state', 'not in', ['draft', 'cancel']),
                      ('number', 'not like', '%_ef%')]
            if context.get('date_from', False):
                domain.append(('date', '>=', context['date_from']))
            # generate where clause to include multicompany rules
            where_query = account_invoice_report._where_calc(cr, uid, domain,
                                                             context=context)
            account_invoice_report._apply_ir_rules(cr, uid, where_query, 'read', context=context)
            from_clause, where_clause, where_clause_params = where_query.get_sql()

            query = """ WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                                SELECT r.currency_id, r.rate, r.name AS date_start,
                                    (SELECT name FROM res_currency_rate r2
                                     WHERE r2.name > r.name AND
                                           r2.currency_id = r.currency_id
                                     ORDER BY r2.name ASC
                                     LIMIT 1) AS date_end
                                FROM res_currency_rate r
                                )
                      SELECT SUM(price_total * cr.rate) as total
                        FROM account_invoice_report account_invoice_report, currency_rate cr
                       WHERE %s
                         AND cr.currency_id = %%s
                         AND (COALESCE(account_invoice_report.date, NOW()) >= cr.date_start)
                         AND (COALESCE(account_invoice_report.date, NOW()) < cr.date_end OR cr.date_end IS NULL)
                    """ % where_clause

            # price_total is in the currency with rate = 1
            # total_invoice should be displayed in the current user's currency
            cr.execute(query, where_clause_params + [user_currency_id])
            result[partner_id] = cr.fetchone()[0]

        return result

    _columns = {
        'total_invoiced_real': fields2.function(_invoice_total_real, string="Total Invoiced", type='float',
                                         groups='account.group_account_invoice'),
        'supplier_all_invoice_count': fields2.function(_purchase_invoice_count, string='# Supplier Invoices',
                                                       type='integer'),
    }


    @api.one
    def _get_products_sold(self):
        lines = self.env["sale.order.line"].read_group([('order_partner_id',
                                                         '=', self.id)],
                                                       ['product_id'],
                                                       groupby="product_id")
        self.sale_product_count = len(lines)

    @api.one
    def _sale_order_count(self):
        self.sale_order_count = len(self.env["sale.order"].
                                    search([('partner_id', 'child_of',
                                             [self.id]),
                                            ('state', 'not in',
                                             ['draft', 'cancel', 'sent'])]))

    @api.one
    def _get_growth_rate(self):
        if self.customer:
            search_date_180 = (date.today() - relativedelta(days=180)).\
                strftime("%Y-%m-%d")
            invoiced_180 = self.with_context(date_from=search_date_180).\
                browse(self.id).total_invoiced_real
            diary_invoice = invoiced_180 / 180.0
            goal = diary_invoice * 15.0
            if goal:
                search_date_15 = (date.today() - relativedelta(days=15)).\
                    strftime("%Y-%m-%d")
                invoiced_15 = self.with_context(date_from=search_date_15).\
                    browse(self.id).total_invoiced_real
                self.growth_rate = invoiced_15 / goal

    @api.one
    def _get_average_margin(self):
        if self.customer:
            margin_avg = 0.0
            total_price = 0.0
            total_cost = 0.0

            d1 = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d")
            final_date = d1.strftime("%Y-%m-%d")
            d2 = d1 - dateutil.relativedelta.relativedelta(months=3)
            start_date = d2.strftime("%Y-%m-%d")

            invoices = self.env['account.invoice'].search(
                [('commercial_partner_id', '=', self.id),
                 ('number', 'not like', '%_ef%'),
                 ('state', 'in', ['paid', 'history', 'open']),
                 ('date_invoice', '>=', start_date),
                 ('date_invoice', '<=', final_date)])

            invoices_line = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', invoices.ids)])

            for i_line in invoices_line:
                self.env.cr.execute("SELECT order_line_id from sale_order_line_invoice_rel" +
                                    " WHERE invoice_id = " + str(i_line.ids[0]))
                order_rel = self.env.cr.fetchone()
                order_line = self.env["sale.order.line"].browse(order_rel)

                if order_line:
                    o_line_data = order_line.read(['purchase_price'])[0]
                    total_price += i_line.quantity * i_line.price_unit * \
                                   ((100.0 - i_line.discount) / 100)
                    total_cost += i_line.quantity * o_line_data['purchase_price']

            if total_price:
                margin_avg = (1 - total_cost / total_price) * 100.0

            self.average_margin = margin_avg

    web = fields.Boolean("Web", help="Created from web", copy=False)
    email_web = fields.Char("Email Web")
    sale_product_count = fields.Integer(compute=_get_products_sold,
                                        string="# Products sold",
                                        readonly=True)
    sale_order_count = fields.Integer(compute="_sale_order_count",
                                      string='# of Sales Order')
    invoice_type_id = fields.Many2one('res.partner.invoice.type',
                                      'Invoice type')
    dropship = fields.Boolean("Dropship")
    send_followup_to_user = fields.Boolean("Send followup to sales agent")
    eur_currency = fields.Many2one('res.currency', default=lambda self: self.env.ref('base.EUR'))
    purchase_quantity = fields.Float('', compute='_get_purchased_quantity')
    att = fields.Char("A/A")
    growth_rate = fields.Float("Growth rate", readonly=True,
                               compute="_get_growth_rate")
    average_margin = fields.Float("Average Margin", readonly=True, compute="_get_average_margin")

    unreconciled_purchase_aml_ids = fields.One2many('account.move.line', 'partner_id',
                                           domain=['&', ('reconcile_id', '=', False), '&',
                                                   ('account_id.active', '=', True), '&',
                                                   ('account_id.type', '=', 'payable'), ('state', '!=', 'draft')])
    _sql_constraints = [
        ('email_web_uniq', 'unique(email_web)', 'Email web field, must be unique')
    ]

    @api.multi
    def _get_purchased_quantity(self):
        for partner in self:
            lines = self.env['purchase.order.line'].search(
                [('order_id.state', '=', 'approved'),
                 ('invoiced', '=', False),
                 ('order_id.partner_id', '=', partner.id)])
            purchases = self.env['purchase.order'].search([('id', 'in', lines.mapped('order_id.id'))])
            total = sum(purchases.mapped('amount_total'))
            partner.purchase_quantity = total

    @api.constrains('ref', 'is_company', 'active')
    def check_unique_ref(self):
        if self.is_company and self.active:
            ids = self.search([('ref', '=', self.ref),
                               ('is_company', '=', True),
                               ('id', '!=', self.id)])
            if ids:
                raise exceptions. \
                    ValidationError(_('Partner ref must be unique'))

    @api.constrains('child_ids', 'is_company', 'active')
    def check_unique_child_ids(self):
        if self.is_company and self.active:
            if not self.child_ids:
                raise exceptions. \
                    ValidationError(_('At least, a contact must be added'))

    @api.constrains('vat', 'is_company', 'supplier', 'customer', 'active')
    def check_unique_vat(self):
        if self.is_company and self.active:
            ids = self.search([('vat', '=', self.vat),
                               ('is_company', '=', True),
                               ('id', '!=', self.id),
                               ('supplier', '=', self.supplier),
                               ('customer', '=', self.customer)])
            if ids:
                raise exceptions. \
                    ValidationError(_('VAT must be unique'))

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company and not record.dropship:
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        if vals.get('dropship', False):
            vals['active'] = False
        if 'web' in vals and not vals['web']:
            vals['email_web'] = None
        vals['date'] = fields.Date.today()
        return super(ResPartner, self).create(vals)

    @api.multi
    @api.constrains('web')
    def check_client_type(self):
        if self.web and self.prospective:
            raise ValidationError(_('The client is prospective. The client cannot be created on the web.'))
        else:
            return True

    @api.multi
    def write(self, vals):
        if self.parent_id.id:
            if not vals.get('lang', False):
                vals['lang'] = self.parent_id.lang
        if vals.get('dropship', False):
            vals['active'] = False
        if 'web' in vals and not vals['web']:
            vals['email_web'] = None
        return super(ResPartner, self).write(vals)

    def _all_lines_get_with_partner(self, cr, uid, partner, company_id, days):
        today = time.strftime('%Y-%m-%d')
        moveline_obj = self.pool['account.move.line']

        domain = [('partner_id', '=', partner.id),
                  ('account_id.type', '=', 'receivable'),
                  ('reconcile_id', '=', False),
                  ('state', '!=', 'draft'),
                  ('company_id', '=', company_id),
                  ('date_maturity', '>', today)]
        if days:
            formatted_date = datetime.strptime(today, "%Y-%m-%d")
            due_date = datetime. \
                strftime(formatted_date + timedelta(days=days), "%Y-%m-%d")
            domain.append(('date_maturity', '<=', due_date))

        moveline_ids = moveline_obj.search(cr, uid, domain)

        # lines_per_currency = {currency: [line data, ...], ...}
        lines_per_currency = defaultdict(list)
        for line in moveline_obj.browse(cr, uid, moveline_ids):
            currency = line.currency_id or line.company_id.currency_id
            invoice_obj = self.pool['account.invoice']
            if line.stored_invoice_id:
                invoice = invoice_obj.browse(cr, uid, line.stored_invoice_id[0].id)
                client_order_ref = invoice.invoice_line[0].move_id.procurement_id.sale_line_id.order_id.client_order_ref
                if not client_order_ref:
                    client_order_ref = ""
            else:
                client_order_ref = ""

            line_data = {
                'name': line.move_id.name,
                'ref': line.ref,
                'date': line.date,
                'date_maturity': line.date_maturity,
                'balance': line.amount_currency if currency != line.company_id.currency_id else line.debit - line.credit,
                'blocked': line.blocked,
                'currency_id': currency,
                'client_order_ref': client_order_ref,
            }
            lines_per_currency[currency].append(line_data)

        return [{'line': lines, 'currency': currency} for currency, lines in lines_per_currency.items()]

    def get_not_followup_table_html(self, cr, uid, ids, days=0, context=None):
        assert len(ids) == 1
        if context is None:
            context = {}
        partner = self.browse(cr, uid, ids[0], context=context).commercial_partner_id
        # copy the context to not change global context. Overwrite it because _() looks for the lang in local variable 'context'.
        # Set the language to use = the partner language
        context = dict(context, lang=partner.lang)
        followup_table = ''
        if partner.unreconciled_aml_ids:
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            current_date = fields2.date.context_today(self, cr, uid, context=context)
            rml_parse = account_followup_print.report_rappel(cr, uid, "followup_rml_parser")
            final_res = self._all_lines_get_with_partner(cr, uid, partner, company.id, days=days)

            for currency_dict in final_res:
                currency = currency_dict.get('line', [{'currency_id': company.currency_id}])[0]['currency_id']
                followup_table += '''
                <table border="2" width=100%%>
                <tr>
                    <td>''' + _("Invoice Date") + '''</td>
                    <td>''' + _("Invoice No.") + '''</td>
                    <td>''' + _("Client Order Ref.") + '''</td>
                    <td>''' + _("Due Date") + '''</td>
                    <td>''' + _("Amount") + " (%s)" % (currency.symbol) + '''</td>
                </tr>
                '''
                total = 0
                for aml in currency_dict['line']:
                    block = aml['blocked'] and 'X' or ' '
                    total += aml['balance']
                    strbegin = "<TD>"
                    strend = "</TD>"
                    date = aml['date_maturity'] or aml['date']
                    followup_table += "<TR>" + strbegin + str(aml['date']) + strend +\
                                      strbegin + (aml['ref'] or '') + strend +\
                                      strbegin + (aml['client_order_ref'] or '') + strend +\
                                      strbegin + str(date) + strend + strbegin +\
                                      str(aml['balance']) + strend + "</TR>"

                total = reduce(lambda x, y: x + y['balance'], currency_dict['line'], 0.00)

                total = rml_parse.formatLang(total, dp='Account', currency_obj=currency)
                followup_table += '''<tr> </tr>
                                </table>
                                <strong><center style="font-size: 18px">''' + _("Amount not due") +\
                                  ''' : %s </center></strong>''' % (total)
        return followup_table

    def get_custom_followup_table_html(self, cr, uid, ids, context=None):
        """ Build the html tables to be included in emails send to partners,
            when reminding them their overdue invoices.
            :param ids: [id] of the partner for whom we are building the tables
            :rtype: string
        """
        assert len(ids) == 1
        if context is None:
            context = {}
        partner = self.browse(cr, uid, ids[0], context=context).commercial_partner_id
        #copy the context to not change global context. Overwrite it because _() looks for the lang in local variable 'context'.
        #Set the language to use = the partner language
        context = dict(context, lang=partner.lang)
        followup_table = ''
        if partner.unreconciled_aml_ids:
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            current_date = fields2.date.context_today(self, cr, uid, context=context)
            rml_parse = account_followup_print.report_rappel(cr, uid, "followup_rml_parser")
            final_res = rml_parse._lines_get_with_partner(partner, company.id)

            for currency_dict in final_res:
                currency = currency_dict.get('line', [{'currency_id': company.currency_id}])[0]['currency_id']
                followup_table += '''
                <table border="2" width=100%%>
                <tr>
                    <td>''' + _("Invoice Date") + '''</td>
                    <td>''' + _("Invoice No.") + '''</td>
                    <td>''' + _("Client Order Ref.") + '''</td>
                    <td>''' + _("Due Date") + '''</td>
                    <td>''' + _("Amount") + " (%s)" % (currency.symbol) + '''</td>
                </tr>
                '''
                total = 0
                for aml in currency_dict['line']:
                    block = aml['blocked'] and 'X' or ' '
                    total += aml['balance']
                    strbegin = "<TD>"
                    strend = "</TD>"
                    date = aml['date_maturity'] or aml['date']
                    if date <= current_date and aml['balance'] > 0:
                        strbegin = "<TD><B>"
                        strend = "</B></TD>"
                    followup_table += "<TR>" + strbegin + str(aml['date']) + strend +\
                                      strbegin + (aml['ref'] or '') + strend +\
                                      strbegin + (aml['client_order_ref'] or '') + strend +\
                                      strbegin + str(date) + strend +\
                                      strbegin + str(aml['balance']) + strend + "</TR>"

                total = reduce(lambda x, y: x+y['balance'], currency_dict['line'], 0.00)

                total = rml_parse.formatLang(total, dp='Account', currency_obj=currency)
                followup_table += '''<tr> </tr>
                                </table>
                                <strong> <center style="font-size: 18px">''' + _("Amount due") \
                                  + ''' : %s </center> </strong>''' % (total)
        return followup_table

class ResPartnerRappelRel(models.Model):

    _inherit = "res.partner.rappel.rel"

    @api.multi
    def _get_invoices(self, period, products):
        res = super(ResPartnerRappelRel, self)._get_invoices(period, products)

        self.ensure_one()
        invoices = self.env['account.invoice'].search(
            [('type', '=', 'out_invoice'),
             ('date_invoice', '>=', period[0]),
             ('date_invoice', '<=', period[1]),
             ('state', 'in', ['open', 'paid']),
             ('commercial_partner_id', '=', self.partner_id.id)])
        refunds = self.env['account.invoice'].search(
            [('type', '=', 'out_refund'),
             ('date_invoice', '>=', period[0]),
             ('date_invoice', '<=', period[1]),
             ('state', 'in', ['open', 'paid']),
             ('commercial_partner_id', '=', self.partner_id.id)])

        # se buscan las rectificativas
        refund_lines = self.env['account.invoice.line'].search(
            [('invoice_id', 'in', [x.id for x in refunds]),
             ('product_id', 'in', products),
             ('no_rappel', '=', False)])
        invoice_lines = self.env['account.invoice.line'].search(
            [('invoice_id', 'in', [x.id for x in invoices]),
             ('product_id', 'in', products),
             ('no_rappel', '=', False)])

        return invoice_lines, refund_lines
