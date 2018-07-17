# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
#   Modulo para la implementacion de los gastos de envios de facturas,
#   cuando creamos una factura desde un albaran.
##############################################################################

from openerp.osv import fields, osv


class sale_order_line(osv.osv):

    def _fnct_line_invoiced(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        for this in self.browse(cr, uid, ids, context=context):
            res[this.id] = this.invoice_lines and \
                           any(iline.invoice_id.state != 'cancel' for iline in this.invoice_lines)
        return res

    def _order_lines_from_invoice(self, cr, uid, ids, context=None):
        # direct access to the m2m table is the less convoluted way to achieve this (and is ok ACL-wise)
        cr.execute("""SELECT DISTINCT sol.id FROM sale_order_invoice_rel rel JOIN
                                                     sale_order_line sol ON (sol.order_id = rel.order_id)
                                       WHERE rel.invoice_id = ANY(%s)""", (list(ids),))
        return [i[0] for i in cr.fetchall()]

    _inherit = 'sale.order.line'
    _columns = {
        'invoiced': fields.function(_fnct_line_invoiced, string='Invoiced', type='boolean',
                                    store={
                                        'account.invoice': (_order_lines_from_invoice, ['state'], 10),
                                        'sale.order.line': (lambda self, cr, uid, ids, ctx=None: ids, ['invoice_lines'], 10)
                                    })
    }


