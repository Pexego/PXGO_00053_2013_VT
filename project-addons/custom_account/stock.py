# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, api, _
from lxml import etree


class StockMove(models.Model):

    _inherit = 'stock.move'

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        res = super(StockMove, self)._get_invoice_line_vals(move, partner, inv_type)
        res['move_id'] = move.id
        return res

    @api.multi
    def unlink(self):
        for move in self:
            if move.state == "confirmed":
                move.state = "draft"
        return super(StockMove, self).unlink()


class ProductProduct(models.Model):

    _inherit = "product.product"

    default_code = fields.Char(required=True)

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code, active)',
         'The code of product must be unique.')
    ]

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None: default = {}
        if not default.get('default_code', False):
            prod = self.browse(cr, uid, id, context=context)
            default['default_code'] = _("%s (copy)") % (prod.default_code)
        return super(ProductProduct, self).copy(cr, uid, id, default=default,
                                                context=context)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s" % record.default_code))
        return result

    def _check_ean_key(self, cr, uid, ids, context=None):
        return True

    _constraints = [(_check_ean_key, 'You provided an invalid "EAN13 Barcode" reference. You may use the "Internal Reference" field instead.', ['ean13'])]


class SaleOrder(models.Model):

    _inherit = "sale.order"

    state = fields.Selection(selection_add=[("history", "History")])
    internal_notes = fields.Text("Internal Notes")

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(SaleOrder, self).\
            fields_view_get(cr, uid, view_id=view_id, view_type=view_type,
                            context=context, toolbar=toolbar, submenu=submenu)
        no_create = context.get('no_create', False)
        update = (no_create and view_type in ['form', 'tree']) or False
        if update:
            doc = etree.XML(res['arch'])
            if no_create:
                for t in doc.xpath("//"+view_type):
                    t.attrib['create'] = 'false'
            res['arch'] = etree.tostring(doc)

        return res


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    state = fields.Selection(selection_add=[("history", "History")])


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    state = fields.Selection(selection_add=[("history", "History")])


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    state = fields.Selection(selection_add=[("history", "History")])


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    state = fields.Selection(selection_add=[("history", "History")])

