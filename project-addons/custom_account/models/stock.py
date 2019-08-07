# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.tools import float_round


class StockMove(models.Model):

    _inherit = 'stock.move'

    @api.multi
    def unlink(self):
        for move in self:
            if move.state == "confirmed":
                move.state = "draft"
        return super().unlink()

    @api.multi
    def _prepare_account_move_line(self, qty, cost, credit_account_id,
                                   debit_account_id):
        self.ensure_one()
        ctx = dict(self.env.context)
        if self.picking_id and \
                self.picking_id.picking_type_id.code == "incoming" and \
                self.picking_id.backorder_id:
            ctx['force_period_date'] = self.picking_id.backorder_id.date_done
        if not cost and not ctx.get('force_valuation_amount') and \
                (self.product_id.standard_price or
                 self.product_id.standard_price_2):
            curr_rounding = self.company_id.currency_id.rounding
            ctx['force_valuation_amount'] = \
                float_round((self.product_id.standard_price or
                             self.product_id.standard_price_2) *
                            self.product_qty, precision_rounding=curr_rounding)
        res = super(StockMove, self.with_context(ctx)).\
            _prepare_account_move_line(qty, cost, credit_account_id,
                                       debit_account_id)

        return res


class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.multi
    def action_view_sales(self):
        res = super().action_view_sales()
        res['domain'] = [('state', 'not in', ['draft', 'cancel']),
                         ('product_id.product_tmpl_id', '=', self.id)]
        return res


class ProductProduct(models.Model):

    _inherit = "product.product"

    default_code = fields.Char(required=True)

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code, active)',
         'The code of product must be unique.')
    ]

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        if not default.get('default_code', False):
            prod = self.browse(self.id)
            default['default_code'] = ("%s (copy)") % (prod.default_code)
            default['name'] = ("%s (copy)") % (prod.name)
        return super(ProductProduct, self).copy(default)

    @api.multi
    def name_get(self):
        partner = self.env['res.partner'].browse(self.env.context.get('partner_id', False))
        result = []
        if partner and partner.supplier:
            for record in self:
                result.append((record.id, "[%s] %s" % ((record.ref_manufacturer or record.default_code), record.default_code)))
        # elif partner:
        #     for record in self:
        #         result.append((record.id, "%s" % record.default_code))
        # elif self.env.context.get('partner', False):
        #     for record in self:
        #         result.append((record.id, "%s" % record.default_code))
        else:
            for record in self:
                result.append((record.id, "%s" % record.default_code))
        return result


class SaleOrder(models.Model):

    _inherit = "sale.order"

    _order = "date_order desc, id desc"

    state = fields.Selection(selection_add=[("history", "History")])
    internal_notes = fields.Text("Internal Notes")
    sale_notes = fields.Text("Sale internal notes")
    partner_tags = fields.Many2many('res.partner.category', column1='sale_id',
                                    column2='category_id', string='Tags')
    ref_partner = fields.Char(related="partner_id.ref",
                              string="Client reference", readonly=True)

    _sql_constraints = [('customer_ref_uniq',
                         'unique(partner_id, client_order_ref)',
                         'Customer ref must be unique by partner')]

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        if self.partner_id:
            self.partner_tags = [(6, 0, self.partner_id.category_id.ids)]
            if self.partner_id.team_id:
                self.team_id = self.partner_id.team_id.id


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    state = fields.Selection(selection_add=[("history", "History")])


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    state = fields.Selection(selection_add=[("history", "History")])


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    state = fields.Selection(selection_add=[("history", "History")])
