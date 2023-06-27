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

    def _is_out(self):
        """se tienen en cuenta las salidas con owner y se evitan las salidas
        a tránsito"""
        res = super()._is_out()
        if not res:
            for move_line in self.move_line_ids.filtered('owner_id'):
                if (move_line.location_id._should_be_valued()
                        and not move_line.location_dest_id.
                        _should_be_valued() and move_line.
                        location_dest_id.usage != 'transit'):
                    return True
        else:
            transit_lines = self.move_line_ids.filtered(
                lambda x: x.location_dest_id.usage == 'transit')
            if transit_lines:
                return False
        return res

    def _is_in(self):
        """se evitan las entradas desde tránsito"""
        res = super()._is_in()
        if res:
            transit_lines = self.move_line_ids.filtered(
                lambda x: x.location_id.usage == 'transit')
            if transit_lines:
                return False
        return res

    def _run_valuation(self, quantity=None):
        value_to_return = super()._run_valuation(quantity=quantity)
        if self._is_out():
            valued_move_lines = self.move_line_ids.filtered(
                lambda ml: ml.location_id._should_be_valued() and not ml.
                location_dest_id._should_be_valued() and ml.owner_id)
            valued_quantity = 0
            company = False
            for valued_move_line in valued_move_lines:
                company = self.env['res.company'].search(
                    [('partner_id', '=', valued_move_line.owner_id.id)],
                    limit=1)
                valued_quantity += valued_move_line.product_uom_id.\
                    _compute_quantity(valued_move_line.qty_done,
                                      self.product_id.uom_id)
            if company:
                value_to_return = self.env['stock.move'].\
                    with_context(candidates_company=company.id)._run_fifo(
                        self.with_context(candidates_company=company.id),
                        quantity=valued_quantity)
                if self.product_id.cost_method in ['standard', 'average']:
                    curr_rounding = self.company_id.currency_id.rounding
                    value = -float_round(
                        self.product_id.standard_price * (valued_quantity
                                                          if quantity is None
                                                          else quantity),
                        precision_rounding=curr_rounding)
                    value_to_return = (
                        value if quantity is None else self.value + value)
                    self.write({
                        'value': value_to_return,
                        'price_unit': value / valued_quantity,
                    })
        return value_to_return

    @api.model
    def _run_fifo(self, move, quantity=None):
        return super(StockMove, self.sudo())._run_fifo(move, quantity=quantity)

    @api.multi
    def _get_accounting_data_for_valuation(self):
        if self._is_out() and self.move_line_ids.filtered('owner_id'):
            company = self.env['res.company'].search(
                [('partner_id', 'in',
                  self.move_line_ids.mapped('owner_id').ids)], limit=1)
            if company:
                return super(StockMove,
                             self.with_context(force_company=company.id)).\
                    _get_accounting_data_for_valuation()
        return super()._get_accounting_data_for_valuation()

    def _create_account_move_line(self, credit_account_id, debit_account_id,
                                  journal_id):
        if self._is_out() and self.move_line_ids.filtered('owner_id'):
            company = self.env['res.company'].search(
                [('partner_id', 'in',
                  self.move_line_ids.mapped('owner_id').ids)], limit=1)
            if company:
                return super(StockMove,
                             self.with_context(force_company=company.id)).\
                    _create_account_move_line(
                        credit_account_id=credit_account_id,
                        debit_account_id=debit_account_id,
                        journal_id=journal_id)
        return super()._create_account_move_line(
            credit_account_id=credit_account_id,
            debit_account_id=debit_account_id,
            journal_id=journal_id)


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
    not_include_report = fields.Boolean(string='Not include in reports')

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code, active)',
         'The code of product must be unique.')
    ]

    def _get_fifo_candidates_in_move(self):
        candidates = super()._get_fifo_candidates_in_move()
        if self.env.context.get('candidates_company'):
            domain = [('product_id', '=', self.id),
                      ('remaining_qty', '>', 0.0),
                      ('company_id', '=',
                       self.env.context['candidates_company'])]
            candidates = self.env['stock.move'].sudo().search(
                domain, order='date, id')
        return candidates

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
            if self.partner_id.warehouse_notes:
                self.internal_notes = self.partner_id.warehouse_notes


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    state = fields.Selection(selection_add=[("history", "History")])


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    state = fields.Selection(selection_add=[("history", "History")])


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    state = fields.Selection(selection_add=[("history", "History")])
