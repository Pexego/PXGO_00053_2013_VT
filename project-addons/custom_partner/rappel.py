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

from openerp import models, fields, api, exceptions, osv, tools, _
from datetime import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta


class rappel_calculated(models.Model):

    _inherit = 'rappel.calculated'

    goal_percentage = fields.Float("Goal Percentage")

    @api.model
    def create_rappel_invoice(self, rappels_to_invoice):
        # Journal = Sales refund (SCNJ)
        journal_obj = self.env['account.journal']
        journal_id = journal_obj.search([('type', '=', 'sale_refund')], order='id')[0].id

        # Prepare context to call action_invoice method
        ctx = dict(self._context or {})
        ctx['active_ids'] = rappels_to_invoice
        ctx['active_id'] = rappels_to_invoice[0]

        rappel_invoice_wzd = self.env['rappel.invoice.wzd']
        new_data_invoice = rappel_invoice_wzd.with_context(ctx).create({'journal_id': journal_id,
                                                                        'group_by_partner': True,
                                                                        'invoice_date': False})
        
        # Create invoice
        new_data_invoice.action_invoice()

        invoice = self.browse(rappels_to_invoice).mapped('invoice_id')

        # Insert negative lines in the created invoice
        if len(rappels_to_invoice) > 1:
            invoice_line_obj = self.env["account.invoice.line"]
            for rp in self.browse(rappels_to_invoice):
                if not rp.invoice_id:
                    rappel_product = rp.rappel_id.type_id.product_id
                    account_id = rappel_product.property_account_income
                    if not account_id:
                        account_id = rappel_product.categ_id. \
                            property_account_income_categ
                    taxes_ids = rappel_product.taxes_id
                    fpos = rp.partner_id.property_account_position or False
                    if fpos:
                        account_id = fpos.map_account(account_id)
                        taxes_ids = fpos.map_tax(taxes_ids)
                    tax_ids = [(6, 0, [x.id for x in taxes_ids])]
                    ctx = dict(rp.rappel_id._context or {})
                    ctx['lang'] = rp.partner_id.lang
                    invoice_line_obj.create({'product_id': rappel_product.id,
                                             'name': u'%s (%s - %s)' %
                                                     (rp.rappel_id.with_context(ctx).description,
                                                      datetime.strptime(rp.date_start, "%Y-%m-%d").strftime('%d/%m/%Y'),
                                                      datetime.strptime(rp.date_end, "%Y-%m-%d").strftime('%d/%m/%Y')),
                                             'invoice_id': invoice.id,
                                             'account_id': account_id.id,
                                             'invoice_line_tax_id': tax_ids,
                                             'price_unit': rp.quantity,
                                             'quantity': 1})
                    rp.invoice_id = invoice.id

        invoice.button_reset_taxes()
        invoice.signal_workflow('invoice_open')

        return True


class ResPartnerRappelRel(models.Model):

    _inherit = "res.partner.rappel.rel"

    @api.multi
    def _get_next_period(self):
        self.ensure_one()
        if self.last_settlement_date and self.last_settlement_date > self.date_start:
            date_start = datetime.strptime(self.last_settlement_date, '%Y-%m-%d').date() + relativedelta(days=1)
        else:
            date_start = datetime.strptime(self.date_start, '%Y-%m-%d').date()

        date_stop = date_start + relativedelta(months=self.PERIODICITIES_MONTHS[self.periodicity], days=-1)
        if self.date_end:
            date_end = datetime.strptime(self.date_end, '%Y-%m-%d').date()
            if date_end < date_stop:
                date_stop = date_end

        if date_start != date_stop:
            period = [date_start, date_stop]
        else:
            period = False

        return period

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

        # Si el rappel afecta al catalago entero, no hacer la comprobacion por producto
        if self.rappel_id.global_application:
            refund_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', [x.id for x in refunds]),
                 ('no_rappel', '=', False)])
            invoice_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', [x.id for x in invoices]),
                 ('no_rappel', '=', False)])
        else:
            refund_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', [x.id for x in refunds]),
                 ('product_id', 'in', products),
                 ('no_rappel', '=', False)])
            invoice_lines = self.env['account.invoice.line'].search(
                [('invoice_id', 'in', [x.id for x in invoices]),
                 ('product_id', 'in', products),
                 ('no_rappel', '=', False)])

        return invoice_lines, refund_lines

    @api.multi
    def _calculate_qty_picking(self):
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        products = self.rappel_id.get_products()
        period = self._get_next_period()
        if period:
            picking_ids = picking_obj.search([('date_done', '>=', period[0].strftime("%Y-%m-%d")),
                                              ('date_done', '<=', period[1].strftime("%Y-%m-%d")),
                                              ('state', '=', 'done'),
                                              ('invoice_state', '=', '2binvoiced'),
                                              ('partner_id', 'child_of', [self.partner_id.id])])

            picking_lines = move_obj.search([('picking_id', 'in', picking_ids.ids),
                                             ('product_id', 'in', products)])

            price_subtotal_lines = picking_lines.mapped('procurement_id.sale_line_id.price_subtotal')
            amount_total = sum([x for x in price_subtotal_lines])
            return amount_total

    @api.model
    def compute(self, period, invoice_lines, refund_lines, tmp_model=False):
        goal_percentage = 0
        rappel_calculated_obj = self.env['rappel.calculated']
        for rappel in self:
            rappel_info = {'rappel_id': rappel.rappel_id.id,
                           'partner_id': rappel.partner_id.id,
                           'date_start': period[0],
                           'amount': 0.0,
                           'amount_est': 0.0,
                           'date_end': period[1]}
            total_rappel = 0.0
            total_rappel_est = 0.0
            if rappel.rappel_id.calc_mode == 'fixed':
                if rappel.rappel_id.calc_amount == 'qty':
                    total_rappel = rappel.rappel_id.fix_qty
                else:
                    total = sum([x.price_subtotal for x in invoice_lines]) - \
                        sum([x.price_subtotal for x in refund_lines])
                    qty_pickings = rappel._calculate_qty_picking()
                    total_est = total + qty_pickings
                    if total:
                        total_rappel = total * rappel.rappel_id.fix_qty / 100.0
                    if total_est:
                        total_rappel_est = total_est * rappel.rappel_id.fix_qty / 100.0
                    rappel_info["curr_qty"] = total
                    rappel_info["curr_qty_pickings"] = qty_pickings

                rappel_info['amount'] = total_rappel
                rappel_info['amount_est'] = total_rappel_est
            else:
                field = ''
                if rappel.rappel_id.qty_type == 'value':
                    field = 'price_subtotal'
                else:
                    field = 'quantity'
                qty_pickings = rappel._calculate_qty_picking()
                total = sum([x[field] for x in invoice_lines]) - \
                    sum([x[field] for x in refund_lines])
                total_est = total + qty_pickings
                rappel_info["curr_qty"] = total
                rappel_info["curr_qty_pickings"] = qty_pickings

                if self.partner_id.invoice_type_id.name in ('Mensual', 'Quincenal', 'Semanal') and total_est:
                    rappel_info, goal_percentage, total_rappel = self.compute_total(rappel, total_est, rappel_info, True)
                else:
                    rappel_info['amount_est'] = 0.0

                if total:
                    rappel_info, goal_percentage, total_rappel = self.compute_total(rappel, total, rappel_info, False)
                else:
                    rappel_info['amount'] = 0.0

            if period[1] <= fields.Date.from_string(fields.Date.today()):
                if total_rappel:
                    rappel_calculated_obj.create({
                        'partner_id': rappel.partner_id.id,
                        'date_start': period[0],
                        'date_end': period[1],
                        'quantity': total_rappel,
                        'rappel_id': rappel.rappel_id.id,
                        'goal_percentage': goal_percentage
                    })
                    if rappel.rappel_id.discount_voucher and total_rappel > 0:
                        rappel_to_invoice = []
                        rappel_old = rappel_calculated_obj.search_read([('partner_id', '=', rappel.partner_id.id),
                                                                        ('rappel_id.discount_voucher', '=', True),
                                                                        ('invoice_id', '=', False)], ['id', 'quantity'])
                        amount_total = 0
                        for rp in rappel_old:
                            rappel_to_invoice.append(rp['id'])
                            amount_total += rp['quantity']
                        if amount_total > 0:
                            rappel_calculated_obj.create_rappel_invoice(rappel_to_invoice)
                rappel.last_settlement_date = period[1]
            else:
                if tmp_model and rappel_info:
                    self.env['rappel.current.info'].create(rappel_info)

        return True

    def compute_total(self, rappel, total, rappel_info, estimated):
        total_rappel = 0.0
        section = self.env['rappel.section'].search(
            [('rappel_id', '=', rappel.rappel_id.id),
             ('rappel_from', '<=', total),
             ('rappel_until', '>=', total)])
        if not section:
            section = self.env['rappel.section'].search(
                [('rappel_id', '=', rappel.rappel_id.id),
                 ('rappel_from', '<=', total),
                 ('rappel_until', '=', False)],
                order='rappel_from desc', limit=1)
        if section:
            goal_percentage = 100
        else:
            # Check if goal percentage is more than 80% to get the rappel
            section = self.env['rappel.section'].search(
                [('rappel_id', '=', rappel.rappel_id.id),
                 ('rappel_from', '<=', total / 0.8),
                 ('rappel_from', '>', total)])
            if section.rappel_from:
                goal_percentage = (total / section.rappel_from) * 100
            else:
                goal_percentage = 0

        if not section:
            if estimated:
                rappel_info['amount_est'] = 0.0
            else:
                rappel_info['amount'] = 0.0
        else:
            rappel_info['section_id'] = section.id
            section = section[0]
            if rappel.rappel_id.calc_amount == 'qty':
                total_rappel = section.percent
            else:
                total_rappel = total * section.percent / 100.0
                if estimated:
                    rappel_info['amount_est'] = total_rappel
                else:
                    rappel_info['amount'] = total_rappel
                    rappel_info['amount_est'] = total_rappel

        return rappel_info, goal_percentage, total_rappel


class rappel(models.Model):

    _inherit = 'rappel'
    brand_ids = fields.Many2many('product.brand', 'rappel_product_brand_rel',
                                 'rappel_id', 'product_brand_id', 'Brand')
    discount_voucher = fields.Boolean('Discount voucher')
    pricelist_ids = fields.Many2many('product.pricelist', 'rappel_product_pricelist_rel',
                                     'rappel_id', 'product_pricelist_id', 'Pricelist')
    description = fields.Char('Description', translate=True)
    sequence = fields.Integer('Sequence', default=100)

    @api.multi
    def get_products(self):
        product_obj = self.env['product.product']
        product_ids = self.env['product.product']
        for rappel in self:
            if not rappel.global_application:
                if rappel.product_id:
                    product_ids += rappel.product_id
                elif rappel.brand_ids:
                    product_ids += product_obj.search(
                        [('product_brand_id', 'in', rappel.brand_ids.ids)])
                elif rappel.product_categ_id:
                    product_ids += product_obj.search(
                        [('categ_id', '=', rappel.product_categ_id.id)])
            else:
                product_ids += product_obj.search([])
        return product_ids.ids

    @api.constrains('global_application', 'product_id', 'brand_ids', 'product_categ_id')
    def _check_application(self):
        if not self.global_application and not self.product_id \
                and not self.product_categ_id and not self.brand_ids:
            raise exceptions. \
                ValidationError(_('Product, brand and category are empty'))

    @api.model
    def update_partner_rappel_pricelist(self):
        partner_obj = self.env['res.partner']
        rappel_obj = self.env['rappel']
        partner_rappel_obj = self.env['res.partner.rappel.rel']
        account_invoice = self.env['account.invoice']

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - relativedelta(days=1)).strftime("%Y-%m-%d")
        end_actual_month = now.strftime("%Y-%m") + '-' + str(monthrange(now.year, now.month)[1])
        start_next_month = (now + relativedelta(months=1)).strftime("%Y-%m") + '-01'

        discount_voucher_rappels = rappel_obj.search([('discount_voucher', '=', True)])
        
        for rappel in discount_voucher_rappels:
            pricelist_ids = tuple(rappel.pricelist_ids.ids)
            product_rappel = rappel.product_id
            # Clientes que ya pertenecen al rappel:
            partner_rappel_list = tuple(partner_rappel_obj.search([('rappel_id', '=', rappel.id),
                                                                   ('date_start', '<=', now_str),
                                                                   '|', ('date_end', '=', False),
                                                                   ('date_end', '>=', now_str)]).mapped('partner_id.id'))
            partner_to_check = tuple()
            if pricelist_ids:
                # Rappels dependientes de tarifas
                # Clientes que deberian pertenecer al rappel:
                partner_to_check = tuple(partner_obj.search([('property_product_pricelist', 'in', pricelist_ids),
                                                             ('prospective', '=', False), ('active', '=', True),
                                                             ('is_company', '=', True), ('parent_id', '=', False)]).ids)

                # Clientes a los que ya no les corresponde el rappel (solo para cambios de tarifa)
                #      - Se actualiza fecha fin con la fecha actual
                remove_partners = set(partner_rappel_list) - set(partner_to_check)
                if remove_partners:
                    vals = {'date_end': yesterday_str}
                    partner_to_update = partner_rappel_obj.search([('rappel_id', '=', rappel.id),
                                                                   ('partner_id', 'in', tuple(remove_partners)),
                                                                   '|', ('date_end', '=', False),
                                                                   ('date_end', '>', now),
                                                                   ('date_start', '<=', now_str)])
                    partner_to_update.write(vals)

            elif product_rappel:
                # Rappel que depende de un producto concreto (y no de la tarifa)
                # Clientes que deberian pertenecer al rappel:
                partner_to_check = tuple(account_invoice.search([('date_invoice', '>=', now_str),
                                                                 ('invoice_line.product_id', '=',
                                                                  product_rappel.id)]).mapped('partner_id.id'))

            #  Clientes que faltan en el rappel -> Se crean dos entradas en el rappel:
            #      - Una para liquidar en el mes actual
            #      - Otra que empiece en fecha 1 del mes siguiente
            add_partners = set(partner_to_check) - set(partner_rappel_list)
            if add_partners:
                new_line1 = {'rappel_id': rappel.id, 'periodicity': 'monthly',
                             'date_start': now_str, 'date_end': end_actual_month}
                new_line2 = {'rappel_id': rappel.id, 'periodicity': 'monthly', 'date_start': start_next_month}
                for partner in add_partners:
                    new_line1.update({'partner_id': partner})
                    partner_rappel_obj.create(new_line1)
                    new_line2.update({'partner_id': partner})
                    partner_rappel_obj.create(new_line2)

    @api.model
    def compute_rappel(self):
        if not self.ids:
            ordered_rappels = self.search([], order='sequence')
        else:
            ordered_rappels = self.sorted(key=lambda x: x.sequence)
        super(rappel, ordered_rappels).compute_rappel()


class RappelCurrentInfo(models.Model):

    _inherit = "rappel.current.info"

    curr_qty_pickings = fields.Float("Qty pending invoice", readonly=True,
                                     help="Qty estimation in pickings pending to be invoiced (shipping cost and"
                                          "product with no-rappel in the order are not verified)")
    amount_est = fields.Float("Estimated amount", readonly=True, default=0.0)

    @api.model
    def send_rappel_info_mail(self):
        mail_pool = self.env['mail.mail']
        mail_ids = self.env['mail.mail']
        partner_pool = self.env['res.partner'].search([('rappel_ids', '!=', '')])
        for partner in partner_pool:
            partner_list = []
            partner_list.append(partner.id)
            pool_partners = self.search([('partner_id', '=', partner.id)])
            send = False
            if pool_partners:

                values = {}
                for rappel in pool_partners:

                    date_end = datetime.strptime(str(rappel.date_end), '%Y-%m-%d')
                    date_start = datetime.strptime(str(rappel.date_start), '%Y-%m-%d')
                    today = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')

                    for rappel_timing in rappel.rappel_id.advice_timing_ids:

                        if rappel_timing.advice_timing == 'fixed':
                            timing = (date_end - today).days
                            if timing == rappel_timing.timing:
                                send = True

                        if rappel_timing.advice_timing == 'variable':

                            timing = (date_end - date_start).days*rappel_timing.timing/100
                            timing2= (today - date_start).days

                            if timing == timing2:
                                send = True

                        if send == True and rappel.curr_qty:
                            if values.get(partner.id):
                                values[partner.id].append ({
                                    'concepto': rappel.rappel_id.name,
                                    'date_start': date_start.strftime('%d/%m/%Y'),
                                    'date_end': date_end.strftime('%d/%m/%Y'),
                                    'advice_timing': rappel_timing.advice_timing,
                                    'timing': rappel_timing.timing,
                                    'curr_qty': rappel.curr_qty,
                                    'section_goal': rappel.section_goal,
                                    'section_id': rappel.section_id,
                                    'amount': rappel.amount
                                })
                            else:
                                values[partner.id] = [{
                                    'concepto': rappel.rappel_id.name,
                                    'date_start': date_start.strftime('%d/%m/%Y'),
                                    'date_end': date_end.strftime('%d/%m/%Y'),
                                    'advice_timing': rappel_timing.advice_timing,
                                    'timing': rappel_timing.timing,
                                    'curr_qty': rappel.curr_qty,
                                    'section_goal': rappel.section_goal,
                                    'section_id': rappel.section_id,
                                    'amount': rappel.amount
                                }]
                        send = False

                if values.get(partner.id):
                    template = self.env.ref('rappel.rappel_mail_advice')
                    ctx = dict(self._context)
                    ctx.update({
                        'partner_email': partner.email,
                        'partner_id': partner.id,
                        'partner_lang': partner.lang,
                        'partner_name': partner.name,
                        'mail_from': self.env.user.company_id.email,
                        'values': values[partner.id]
                    })

                    mail_id = template.with_context(ctx).send_mail(rappel.partner_id.id)
                    mail_ids += mail_pool.browse(mail_id)
        if mail_ids:
            mail_ids.send()


class ComputeRappelInvoice(models.TransientModel):

    _inherit = "rappel.invoice.wzd"

    @api.multi
    def action_invoice(self):
        res = super(ComputeRappelInvoice, self).action_invoice()
        compute_rappel_obj = self.env["rappel.calculated"]
        for rappel in compute_rappel_obj.browse(self.env.context["active_ids"]):
            if rappel.quantity <= 0:
                continue
            if rappel.invoice_id:
                invoice_rappel = rappel.invoice_id
                # Update description invoice lines
                for line in invoice_rappel.invoice_line:
                    ctx = dict(rappel.rappel_id._context or {})
                    ctx['lang'] = rappel.partner_id.lang
                    line.write({'name': u'%s (%s - %s)' %
                                        (rappel.rappel_id.with_context(ctx).description,
                                         datetime.strptime(rappel.date_start, "%Y-%m-%d").strftime('%d/%m/%Y'),
                                         datetime.strptime(rappel.date_end, "%Y-%m-%d").strftime('%d/%m/%Y'))})
                # Update account data
                if not invoice_rappel.payment_mode_id \
                        or not invoice_rappel.partner_bank_id \
                        or not invoice_rappel.section_id:
                    partner_bank_id = False
                    for banks in rappel.partner_id.bank_ids:
                        for mandate in banks.mandate_ids:
                            if mandate.state == 'valid':
                                partner_bank_id = banks.id
                                break
                            else:
                                partner_bank_id = False
                    invoice_rappel.write({'payment_mode_id': rappel.partner_id.customer_payment_mode.id,
                                          'partner_bank_id': partner_bank_id,
                                          'section_id': rappel.partner_id.section_id.id})
        return res
