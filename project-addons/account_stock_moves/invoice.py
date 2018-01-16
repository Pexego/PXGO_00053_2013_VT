# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C)
#    2004-2010 Tiny SPRL (<http://tiny.be>).
#    2009-2010 Veritos (http://veritos.nl).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import orm


class account_invoice_line(orm.Model):
    _inherit = "account.invoice.line"

    def move_line_get_item(self, cr, uid, line, context=None):
        uom_obj = self.pool.get('product.uom')
        res = super(account_invoice_line, self).move_line_get_item(
            cr, uid, line, context=context)
        moves_price = 0.0
        total_qty = 0.0

        if line.move_id and line.product_id.valuation == 'real_time' and \
                line.move_id.picking_id.picking_type_code == 'incoming':
            move = line.move_id
            qty = uom_obj._compute_qty(cr, uid, move.product_uom.id,
                                       move.product_qty,
                                       move.product_id.uom_id.id)
            total_qty += qty
            if move.product_id.cost_method in ['average', 'real'] \
                    and (move.price_unit or
                         (move.purchase_line_id and
                          not move.purchase_line_id.price_subtotal)):
                price_unit = move.price_unit
                moves_price += price_unit * qty
            else:
                price_unit = move.product_id.standard_price
                moves_price += price_unit * qty
            res['price_move'] = moves_price
            res['move_id'] = move.id
            if move.purchase_line_id and move.picking_id and \
                    move.picking_id.backorder_id:
                res['create_date'] = move._get_origin_create_date()
            else:
                res['create_date'] = move.create_date
            if total_qty > 0:
                res['price_unit'] = moves_price / total_qty
            else:
                res['price_unit'] = 0
        return res

    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = super(account_invoice_line, self).move_line_get(
            cr, uid, invoice_id, context=context)
        inv = self.pool.get('account.invoice').browse(
            cr, uid, invoice_id, context=context)
        currency_obj = self.pool.get('res.currency')
        if inv.type in ('in_invoice', 'in_refund'):
            for i_line in inv.invoice_line:
                company_currency = i_line.invoice_id.company_id.currency_id.id
                if i_line.product_id \
                    and i_line.product_id.valuation == 'real_time' \
                        and i_line.product_id.type != 'service' and \
                        i_line.move_id:
                    # get the price difference account at the product
                    acc = i_line.product_id.\
                        property_account_creditor_price_difference \
                        and i_line.product_id.\
                        property_account_creditor_price_difference.id
                    if not acc:
                        # if not found on the product get the price
                        # difference account at the category
                        acc = i_line.product_id.categ_id.\
                            property_account_creditor_price_difference_categ \
                            and i_line.product_id.categ_id.\
                            property_account_creditor_price_difference_categ.id
                    a = None

                    # oa will be the stock input account
                    # first check the product, if empty check the category
                    oa = i_line.product_id.property_stock_account_input \
                        and i_line.product_id.property_stock_account_input.id
                    if not oa:
                        oa = i_line.product_id.categ_id.\
                            property_stock_account_input_categ \
                            and i_line.product_id.categ_id.\
                            property_stock_account_input_categ.id

                    if oa:
                        # get the fiscal position
                        fpos = i_line.invoice_id.fiscal_position or False
                        a = self.pool.get('account.fiscal.position').\
                            map_account(cr, uid, fpos, oa)
                    diff_res = []
                    # calculate and write down the possible price difference
                    # between invoice price and product price
                    for line in res:
                        if 'move_id' in line and \
                                i_line.move_id.id == line['move_id']:

                            if 'price_move' in line and line['price_move'] != \
                                    i_line.price_subtotal and acc:
                                price_subtotal = currency_obj.\
                                    compute(cr, uid,
                                            i_line.invoice_id.currency_id.id,
                                            company_currency,
                                            i_line.price_subtotal,
                                            round=True,
                                            context={'date':
                                                     line['create_date']})
                                price_diff = \
                                    price_subtotal - line['price_move']
                                if not price_diff or price_diff <= 0.01:
                                    continue
                                diff_res.append({
                                    'type': 'sto',
                                    'name': i_line.name[:64],
                                    'price_unit': price_diff,
                                    'quantity': line['quantity'],
                                    'price': price_diff,
                                    'account_id': acc,
                                    'product_id': line['product_id'],
                                    'uos_id': line['uos_id'],
                                    'account_analytic_id':
                                    line['account_analytic_id'],
                                    'taxes': line.get('taxes', []),
                                    })
                                diff_res.append({
                                    'type': 'sto',
                                    'name': i_line.name[:64],
                                    'price_unit': -price_diff,
                                    'quantity': line['quantity'],
                                    'price': -price_diff,
                                    'account_id': a,
                                    'product_id': line['product_id'],
                                    'uos_id': line['uos_id'],
                                    'account_analytic_id':
                                    line['account_analytic_id'],
                                    'taxes': line.get('taxes', []),
                                    })
                    res += diff_res
            print res
        return res
