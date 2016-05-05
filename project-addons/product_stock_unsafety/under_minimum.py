# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
from openerp.osv import osv, fields
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
STATES = [('in_progress', 'In Progress'),
          ('in_action', 'In Action'),
          ('finalized', 'Finalized'),
          ('exception', 'Exception'),
          ('cancelled', 'Cancelled')]


class product_stock_unsafety(osv.Model):
    _name = 'product.stock.unsafety'
    _description = 'Products that have stock under minimum'
    _order = 'id desc'
    _columns = {
        'product_id': fields.many2one('product.product',
                                      'Product',
                                      readonly=True,
                                      required=True),
        'orderpoint_id': fields.many2one('stock.warehouse.orderpoint',
                                         'Replenishement Rule',
                                         readonly=True,
                                         required=True,
                                         ondelete='cascade',
                                         help='The replenishement rule that '
                                         'launch this under minimum alert.'),
        'supplier_id': fields.many2one('res.partner',
                                       'Supplier',
                                       readonly=True),
        'remaining_days_sale': fields.related('product_id',
                                              'remaining_days_sale',
                                              type='float',
                                              string='Remaining Days of Sale',
                                              readonly=True),
        'real_stock': fields.related('product_id', 'qty_available',
                                     type='float',
                                     string='Real Stock',
                                     readonly=True,
                                     help='Quantity in stock'),
        'virtual_stock': fields.related('product_id',
                                        'virtual_stock_conservative',
                                        type='float',
                                        string='Virtual Stock Conservative',
                                        readonly=True,
                                        help='Real stock - outgoings '),
        'virtual_available': fields.related('product_id',
                                            'virtual_available',
                                            type='float',
                                            string='Quantity available',
                                            readonly=True,
                                            help='Real stock + incomings - '
                                            'outgongs'),
        'purchase_id': fields.many2one('purchase.order',
                                       'Purchase', readonly=True),
        'product_qty': fields.float('Qty ordered'),
        # 'date_delivery': fields.date('Delivery', readonly=True),
        'responsible': fields.many2one('res.users',
                                       'Responsible', readonly=True),
        'state': fields.selection(STATES, 'State', readonly=True),
        'date': fields.date('Date', readonly=True),
        'name': fields.char('Reason', size=64, readonly=True),
        'incoming_qty': fields.related('product_id',
                                       'incoming_qty',
                                       type='float',
                                       string='Incoming qty.',
                                       readonly=True,
                                       help='Quantity pending to recive'),
        'minimum_proposal': fields.float('Min. Proposal',
                                         readonly=True,
                                         help='Quantity necessary to reach '
                                         'the minimum days of purchase'),
        'product_type': fields.selection([("manufacture", "To manufacture"),
                                          ("buy", "To buy")], "Product type",
                                         required=True),
        'bom_id': fields.many2one("mrp.bom", "Bill of material",
                                  readonly=True)
    }
    _defaults = {
        'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('minimum_proposal', False):
            vals['product_qty'] = vals['minimum_proposal']
        return super(product_stock_unsafety, self).create(cr, uid, vals,
                                                          context)

    def cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state': 'cancelled'})
        return True

    # def write_purchase_id(self, cr, uid, ids, purchase_line_id=False,
    #                       product_id=False, context=None):
    #     """
    #     Function you are looking if exists under minimum for he product
    #     received in progress state and has not linked purchase order line.
    #     If found, writes it the purchase order line that just created.
    #     """
    #     if context is None:
    #         context = {}
    #     mins = []
    #     undermin = self.pool.get('product.stock.unsafety')
    #     purl = self.pool.get('purchase.order.line')
    #     if product_id and purchase_line_id:
    #         # Find under minimums that satisfying the conditions
    #         # indicated.
    #         mins = undermin.search(cr, uid, [('product_id', '=', product_id),
    #                                          ('state', '=', 'in_progress'),
    #                                          ('purchase_id', '=', False)])
    #         if mins:
    #             # Writes the first under minimum found the purchase
    #             # order line that was just created
    #             purline = purl.browse(cr, uid, purchase_line_id)
    #             undermin.write(cr,
    #                            uid,
    #                            mins[0],
    #                            {'purchase_id': purchase_line_id,
    #                             'product_qty': purline.product_qty})
    #     return {}
