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

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        for move in self:
            if move.location_id.usage == "customer" and \
                    move.location_dest_id.usage == "internal":
                for quant in move.quant_ids:
                    quantS = self.sudo().env["stock.quant"].browse(quant.id)
                    quantS.cost = quant.product_id.standard_price

        return res


class ProductProduct(models.Model):

    _inherit = "product.product"

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

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code, active)',
         'The code of product must be unique.')
    ]

    # def copy(self, cr, uid, id, default=None, context=None):
    #     if default is None: default = {} TODO: Migrar
    #     if not default.get('default_code', False):
    #         prod = self.browse(cr, uid, id, context=context)
    #         default['default_code'] = _("%s (copy)") % (prod.default_code)
    #     return super(ProductProduct, self).copy(cr, uid, id, default=default,
    #                                             context=context)

    @api.multi
    def name_get(self):
        partner_id = self.env.context.get('partner_id', False)
        result = []
        for record in self:
            sellers = [x.name.id for x in record.seller_ids]
            if partner_id and partner_id in sellers:
                result.extend(super(ProductProduct, self).name_get())
            else:
                result.append((record.id, "%s" % record.default_code))
        return result

    def _check_ean_key(self, cr, uid, ids, context=None):
        return True

    _constraints = [(_check_ean_key, 'You provided an invalid "EAN13 Barcode" reference. You may use the "Internal Reference" field instead.', ['ean13'])]


class ProductTemplate(models.Model):

    _inherit = "product.template"

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

    @api.multi
    def action_view_stock_moves(self):
        res = super(ProductTemplate, self).action_view_stock_moves()
        product_ids = []
        for template in self:
            product_ids += [x.id for x in template.product_variant_ids]
        res['domain'] = "[('product_id','in',[" + \
            ','.join(map(str, product_ids)) + \
            "]),('picking_type_code', '=', 'incoming')]"

        if len(product_ids) == 1:
            ctx = "{'tree_view_ref':'stock.view_move_tree', \
                  'default_product_id': %s, 'search_default_product_id': %s, 'search_default_ready': 1,'search_default_future': 1}" \
                  % (product_ids[0], product_ids[0])
            res['context'] = ctx
        else:
            res['context'] = "{'tree_view_ref':'stock.view_move_tree', 'search_default_ready': 1,'search_default_future': 1}"
        return res


class SaleOrder(models.Model):

    _inherit = "sale.order"

    _order = "date_order desc, id desc"

    state = fields.Selection(selection_add=[("history", "History")])
    internal_notes = fields.Text("Internal Notes")
    sale_notes = fields.Text("Sale internal notes")
    partner_tags = fields.Many2many('res.partner.category', column1='sale_id',
                                    column2='category_id', string='Tags')
    ref_partner = fields.Char(related="partner_id.ref", string="Client reference", readonly=True)

    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
        return fields.Datetime.now()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(SaleOrder, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        no_create = self.env.context.get('no_create', False)
        update = (no_create and view_type in ['form', 'tree']) or False
        if update:
            doc = etree.XML(res['arch'])
            if no_create:
                for t in doc.xpath("//"+view_type):
                    t.attrib['create'] = 'false'
            res['arch'] = etree.tostring(doc)

        return res

    _sql_constraints = [('customer_ref_uniq',
                         'unique(partner_id, client_order_ref)',
                         'Customer ref must be unique by partner')]

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(SaleOrder, self).onchange_partner_id(cr, uid, ids, part,
                                                         context=context)
        if part and res.get('value', False):
            partner = self.pool['res.partner'].browse(cr, uid, part)
            res['value']['partner_tags'] = [(6, 0, [x.id for x in partner.category_id])]
            if partner.section_id:
                res['value']['section_id'] = partner.section_id.id

        return res

    # def copy(self, cr, uid, id, default={}, context=None):
    #     sale = self.browse(cr, uid, id, context) TODO: Migrar
    #     if sale.client_order_ref:
    #         default['client_order_ref'] = sale.client_order_ref + _(" (copy)")
    #     result = super(SaleOrder, self).copy(cr, uid, id, default, context)

    #     return result


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    state = fields.Selection(selection_add=[("history", "History")])


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    state = fields.Selection(selection_add=[("history", "History")])


#TODO: Migrar
# ~ class PurchaseLineInvoice(models.TransientModel):

    # ~ _inherit = "purchase.order.line_invoice"

    # ~ @api.model
    # ~ def _make_invoice_by_partner(self, partner, orders, lines_ids):
        # ~ inv_id = super(PurchaseLineInvoice, self).\
            # ~ _make_invoice_by_partner(partner, orders, lines_ids)
        # ~ invoice = self.env["account.invoice"].browse(inv_id)
        # ~ invoice.payment_mode_id = partner.supplier_payment_mode.id
        # ~ invoice.button_reset_taxes()
        # ~ return inv_id


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    state = fields.Selection(selection_add=[("history", "History")])


class StockQuant(models.Model):

    _inherit = "stock.quant"

    @api.model
    def _prepare_account_move_line(self, move, qty, cost, credit_account_id,
                                   debit_account_id):
        ctx = dict(self.env.context)
        if move.picking_id and \
                move.picking_id.picking_type_id.code == "incoming" and \
                move.picking_id.backorder_id:
            ctx['date'] = move.picking_id.backorder_id.date_done

        res = super(StockQuant, self.with_context(ctx)).\
            _prepare_account_move_line(move, qty, cost, credit_account_id,
                                       debit_account_id)
        currency_obj = self.pool.get('res.currency')
        if not self.env.context.get('force_valuation_amount', False) and \
                move.product_id.cost_method == 'real' and \
                move.location_id.usage == "customer" and \
                move.location_dest_id.usage == "internal":
            valuation_amount = \
                currency_obj.round(self._cr, self._uid,
                                   move.company_id.currency_id,
                                   move.product_id.standard_price * qty)
            res[0][2]['debit'] = valuation_amount > 0 and valuation_amount \
                or 0
            res[0][2]['credit'] = valuation_amount < 0 and -valuation_amount \
                or 0
            res[1][2]['debit'] = valuation_amount < 0 and -valuation_amount \
                or 0
            res[1][2]['credit'] = valuation_amount > 0 and valuation_amount \
                or 0

        return res


#TODO: Migrar
# ~ class WizardValuationHistory(models.TransientModel):

    # ~ _inherit = 'wizard.valuation.history'

    # ~ @api.multi
    # ~ def open_table(self):
        # ~ locations = []
        # ~ res = super(WizardValuationHistory, self).open_table()
        # ~ data = self.read()[0]
        # ~ locations.append(self.env.ref("crm_rma_advance_location.stock_location_rma").id)
        # ~ locations.append(self.env.ref("location_moves.stock_location_damaged").id)
        # ~ res['domain'] = "[('date', '<=', '" + data['date'] + "'),('location_id', 'not in', " + str(locations) + ")]"
        # ~ return res
