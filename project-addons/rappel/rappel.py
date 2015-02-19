# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2015 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class rappel(models.Model):
    _name = 'rappel'
    _description = 'Rappel Model'
    PERIODICITIES = [('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
                     ('semiannual', 'Semiannual'), ('annual', 'Annual')]
    PERIODICITIES_MONTHS = {'monthly': 1, 'quarterly': 3, 'semiannual': 6,
                            'annual': 12}
    CALC_MODE = [('fixed', 'Fixed'), ('variable', 'Variable')]
    QTY_TYPE = [('quantity', 'Quantity'), ('Value', 'value')]
    CALC_AMOUNT = [('percent', 'Percent'), ('qty', 'Quantity')]

    name = fields.Char('Concept', size=255, required=True)
    type_id = fields.Many2one('rappel.type', 'Type', required=True)
    date_start = fields.Date('Date Start', required=True)
    date_stop = fields.Date('Date Stop')
    qty_type = fields.Selection(QTY_TYPE, 'Quantity type', required=True)
    periodicity = fields.Selection(PERIODICITIES,
                                   'Periodicity',
                                   required=True)
    calc_mode = fields.Selection(CALC_MODE, 'Fixed/Variable', required=True)
    fix_qty = fields.Float('Fix')
    sections = fields.One2many('rappel.section', 'rappel_id', 'Sections')
    global_application = fields.Boolean('Global', default=True)
    product_id = fields.Many2one('product.product', 'Product')
    product_categ_id = fields.Many2one('product.category', 'Category')
    calc_amount = fields.Selection(CALC_AMOUNT, 'Percent/Quantity',
                                   required=True)
    last_execution = fields.Date('Last execution')
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)

    @api.model
    def create(self, vals):
        if vals['global_application'] is False:
            if not vals['product_id'] and not vals['product_categ_id']:
                raise exceptions.Warning(_('Error'),
                                         _('Product and category are empty'))
        return super(rappel, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(rappel, self).write(vals)
        keys = vals.keys()
        if 'global_application' in keys or 'product_id' in keys or \
                'product_categ_id' in keys:
            for rappel_o in self:
                if rappel_o['global_application'] is False:
                    if not rappel_o['product_id'] and not \
                            rappel_o['product_categ_id']:
                        raise exceptions.Warning(_('Error'),
                                                 _('Product and category are \
empty'))
        return res

    @api.multi
    def get_products(self):
        product_obj = self.env['product.product']
        product_ids = self.env['product.product']
        for rappel in self:
            if not rappel.global_application:
                if rappel.product_categ_id:
                    product_ids = \
                        [x.id for x in product_obj.search(
                            [('categ_id', '=', rappel.product_categ_id.id)])]
                if rappel.product_id:
                    product_ids = [rappel.product_id.id]
            else:
                product_ids = [x.id for x in product_obj.search([])]
        return product_ids

    @api.multi
    def _get_periods(self):
        if self.last_execution and self.last_execution > self.date_start:
            date_start = \
                datetime.strptime(self.last_execution, '%Y-%m-%d').date()
        else:
            date_start = \
                datetime.strptime(self.date_start, '%Y-%m-%d').date()
        if self.date_stop:
            date_stop = datetime.strptime(self.date_stop, '%Y-%m-%d').date()
        else:
            date_stop = date.today() + relativedelta(months=3)
        periods = []
        date_aux = date_start
        while date_aux < date_stop:
            start = date_aux
            end = date_aux + \
                relativedelta(months=self.PERIODICITIES_MONTHS[self.periodicity]) + relativedelta(days=-1)
            date_aux = date_aux + \
                relativedelta(months=self.PERIODICITIES_MONTHS[self.periodicity])
            period = (start, end)
            if end <= date_stop and end <= date.today():
                periods.append(period)
        return periods

    @api.multi
    def create_calculation(self, period, invoice_lines, refund_lines):
        total_rappel = 0.0
        if self.calc_mode == 'fixed':
            if self.calc_amount == 'qty':
                total_rappel = self.fix_qty
            else:
                total = sum([x.price_subtotal for x in invoice_lines]) - \
                    sum([x.price_subtotal for x in refund_lines])
                total_rappel = total * self.fix_qty / 100
        else:
            field = ''
            if self.qty_type == 'value':
                field = 'price_subtotal'
            else:
                field = 'quantity'
            total = sum([x[field] for x in invoice_lines]) - \
                sum([x[field] for x in refund_lines])
            if total == 0:
                return True
            section = self.env['rappel.section'].search(
                [('rappel_id', '=', self.id), ('rappel_from', '<=', total),
                 ('rappel_until', '>=', total)])
            if not section:
                section = self.env['rappel.section'].search(
                    [('rappel_id', '=', self.id),
                     ('rappel_from', '<=', total)], order='rappel_until desc')
                if not section:
                    return True
            section = section[0]
            if self.calc_amount == 'qty':
                total_rappel = section.percent
            else:
                total = sum([x.price_subtotal for x in invoice_lines]) - \
                    sum([x.price_subtotal for x in refund_lines])
                total_rappel = total * section.percent / 100
        if total_rappel:
            self.env['rappel.calculated'].create({
                'partner_id': self.partner_id.id,
                'date_start': period[0],
                'date_end': period[1],
                'quantity': total_rappel,
                'rappel_id': self.id
            })
        return True

    @api.model
    def calculate_rappel(self):
        today = date.today()
        for rappel in self.search([('date_start', '<', today)]):
            if (today +
                    relativedelta(months=-self.PERIODICITIES_MONTHS[rappel.periodicity])).strftime('%Y-%m-%d') > rappel.date_stop:
                continue
            periods = rappel._get_periods()
            products = rappel.get_products()
            for period in periods:
                invoices = self.env['account.invoice'].search(
                    [('type', '=', 'out_invoice'),
                     ('date_invoice', '>=', period[0]),
                     ('date_invoice', '<=', period[1]),
                     ('state', '=', 'paid'),
                     ('partner_id', '=', rappel.partner_id.id)])

                # se buscan las rectificativas
                refund_lines = self.env['account.invoice.line']
                invoice_ids = []
                for invoice in invoices:
                    refunds = self.env['account.invoice'].search(
                        [('type', '=', 'out_refund'),
                         ('state', '=', 'paid'),
                         ('origin_invoices_ids', '=', invoice.id)])
                    refund_lines += self.env['account.invoice.line'].search(
                        [('invoice_id', 'in', [x.id for x in refunds]),
                         ('product_id', 'in', products)])
                    invoice_ids.append(invoice.id)
                invoice_lines = self.env['account.invoice.line'].search(
                    [('invoice_id', 'in', invoice_ids),
                     ('product_id', 'in', products)])
                rappel.create_calculation(period, invoice_lines, refund_lines)
            if periods:
                rappel.last_execution = periods[-1][1]


class rappel_section(models.Model):

    _name = 'rappel.section'
    _description = 'Rappel section model'

    rappel_from = fields.Float('From')
    rappel_until = fields.Float('Until')
    percent = fields.Float('Value')
    rappel_id = fields.Many2one('rappel', 'Rappel')


class rappel_calculated(models.Model):

    _name = 'rappel.calculated'
    partner_id = fields.Many2one('res.partner', 'Customer')
    date_start = fields.Date('Date start')
    date_end = fields.Date('Date end')
    quantity = fields.Float('Quantity')
    rappel_id = fields.Many2one('rappel', 'Rappel')
