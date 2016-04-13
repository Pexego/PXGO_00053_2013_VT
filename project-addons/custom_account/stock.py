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

    @api.one
    def _sales_count(self):
        domain = [
            ('state', 'not in', ['cancel', 'draft']),
            ('product_id', '=', self.id),
        ]
        group = self.env['sale.report'].\
            read_group(domain, ['product_id', 'product_uom_qty'],
                       ['product_id'])[0]
        self.sales_count = group['product_uom_qty']

    @api.one
    def _quotations_count(self):
        domain = [
            ('state', '=', 'draft'),
            ('product_id', '=', self.id),
        ]
        group = self.env['sale.report'].\
            read_group(domain, ['product_id', 'product_uom_qty'],
                       ['product_id'])[0]
        self.quotations_count = group['product_uom_qty']

    @api.multi
    def action_view_sales(self):
        res = super(ProductProduct, self).action_view_sales()
        res['domain'] = "[('product_id','in',[" + \
            ','.join(map(str, self.ids)) + \
            "]),('state', 'not in', ['cancel', 'draft'])]"
        return res

    @api.multi
    def action_view_quotations(self):
        res = super(ProductProduct, self).action_view_sales()
        res['domain'] = "[('product_id','in',[" + \
            ','.join(map(str, self.ids)) + \
            "]),('state', '=', 'draft')]"
        return res

    default_code = fields.Char(required=True)
    sales_count = fields.Integer(compute="_sales_count", string='# Sales')
    quotations_count = fields.Integer(compute="_quotations_count",
                                      string='# Quotations')

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


class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.multi
    def _quotations_count(self):
        for template in self:
            template.quotations_count = \
                sum([p.sales_count for p in template.product_variant_ids])

    quotations_count = fields.Integer(compute="_quotations_count",
                                      string='# Sales')

    @api.multi
    def action_view_sales(self):
        res = super(ProductTemplate, self).action_view_sales()
        product_ids = []
        for template in self:
            product_ids += [x.id for x in template.product_variant_ids]
        res['domain'] = "[('product_id','in',[" + \
            ','.join(map(str, product_ids)) + \
            "]),('state', 'not in', ['draft', 'cancel'])]"
        return res

    @api.multi
    def action_view_quotations(self):
        res = super(ProductTemplate, self).action_view_sales()
        product_ids = []
        for template in self:
            product_ids += [x.id for x in template.product_variant_ids]
        res['domain'] = "[('product_id','in',[" + \
            ','.join(map(str, product_ids)) + \
            "]),('state', '=', 'draft')]"
        return res


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

