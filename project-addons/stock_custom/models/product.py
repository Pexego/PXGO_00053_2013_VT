# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _, exceptions
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    name = fields.Char(translate=False)

    description = fields.Text(copy=False)
    observations = fields.Text(
        'Observations', translate=True,
        help="Aditional notes for the product.")
    description_sale = fields.Text(copy=False)
    description_purchase = fields.Text(copy=False)
    description_pickingout = fields.Text(copy=False)
    description_pickingin = fields.Text(copy=False)
    description_picking = fields.Text(copy=False)
    sale_line_warn = fields.Selection(copy=False)
    purchase_line_warn = fields.Selection(copy=False)

    currency_purchase_id = fields.Many2one('res.currency', 'Currency',
                                           default=lambda self: self.env.user.company_id.currency_id.id)
    track_serial = fields.Boolean("Track Serials")

    @api.model
    def create(self, vals):
        prod = super().create(vals)
        prod.property_valuation = prod.categ_id.property_valuation
        if self.env.user.company_id.country_id.code == 'IT':
            if not prod.seller_ids:
                supplierinfo = self.env['product.supplierinfo'].create({
                    'name': 27,
                    'min_qty': 1
                })
                prod.seller_ids = supplierinfo
            prod.last_supplier_id = prod.seller_ids[0].name.id
        return prod

    def set_product_template_currency_purchase(self, currency):
        self.currency_purchase_id = currency


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def _get_deposit_stock(self):
        company = self.env.user.company_id
        quants = self.env['stock.quant'].sudo().read_group(
            [('product_id', 'in', self.ids),
             ('location_id.usage', 'in', ['internal', 'transit']),
             ('owner_id', '=', company.partner_id.id)],
            ['product_id', 'quantity'], ['product_id'])
        quants = {x['product_id'][0]: x['quantity'] for x in quants}
        for product in self:
            if quants.get(product.id):
                product.qty_available_deposit = quants[product.id]
            else:
                product.qty_available_deposit = 0.0

    ref_visiotech = fields.Char('Visiotech reference')
    is_pack = fields.Boolean()
    qty_available_deposit = fields.\
        Float(string="Qty. on deposit", compute="_get_deposit_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))

    def action_view_moves(self):
        return {
            'domain': "[('product_id','=', " + str(self.id) + ")]",
            'name': _('Stock moves'),
            'view_mode': 'tree',
            'view_type': 'form',
            'context': {'tree_view_ref': 'stock.view_move_tree',
                        'search_default_groupby_dest_location_id': 1,
                        'search_default_ready': 1,
                        'search_default_future': 1},
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
        }

    def action_view_moves_dates(self):
        return {
            'domain': "[('product_id','=', " + str(self.id) + ")]",
            'name': _('Stock moves dates'),
            'view_mode': 'tree',
            'view_type' : 'form',
            'context': {'tree_view_ref': 'stock_custom.view_move_dates_tree',
                        'search_default_future_dates': 1},
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
        }

    def action_view_deposit_stock_report(self):
        return {
            'domain': [('product_id', '=', self.id),
                       ('owner_id', '=',
                        self.env.user.company_id.partner_id.id)],
            'name': _('Deposit stock report'),
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': 'stock.deposit.report',
            'type': 'ir.actions.act_window',
        }

    def get_stock_new(self):
        category_id = self.env['product.category'].search(
            [('name', '=', 'NUEVOS')])
        products = self.env['product.product'].search(
            [('categ_id', '=', category_id.id)])
        ids_products = [x.id for x in products
                        if x.qty_available > 0]
        return {
            'domain': "[('id','in', " + str(ids_products) + ")]",
            'name': _('Stock New'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def _compute_date_first_incoming(self):
        for product in self:
            moves = self.env['stock.move'].search(
                [('product_id', '=', product.id), ('picking_id', '!=', False),
                 ('purchase_line_id', '!=', False),('state','=','done'),('date_done','!=',False)],order='date_done asc', limit=1)
            if moves:
                product.date_first_incoming = moves.date_done
                product.date_first_incoming_reliability = "1.received"
            else:
                moves = self.env['stock.move'].search(
                    [('product_id', '=', product.id), ('purchase_line_id', '!=', False), ('state','!=','cancel')]).sorted(
                    key=lambda m: m.date_expected and m.date_reliability)
                if moves:
                    reliability = moves[0].date_reliability[1::]
                    number_reliability = str(int(moves[0].date_reliability[0]) + 1)
                    product.date_first_incoming_reliability = number_reliability+reliability
                    product.date_first_incoming = moves[0].date_expected

    date_first_incoming = fields.Datetime(compute=_compute_date_first_incoming, store=True)

    date_first_incoming_reliability = fields.Selection([
        ('1.received', 'Received'),
        ('2.high', 'High'),
        ('3.medium', 'Medium'),
        ('4.low', 'Low'),
        ])

    currency_purchase_id = fields.Many2one('res.currency', 'Currency',
                                           default=lambda self: self.env.user.company_id.currency_id.id)

    last_purchase_price = fields.Monetary(currency_field="currency_purchase_id", copy=False)
    last_supplier_id = fields.Many2one(
        comodel_name='res.partner', string='Last Supplier', copy=False)
    last_landed_cost_date = fields.Date('Last LC date')

    @api.multi
    def set_product_last_purchase(self, order_id=False):
        res = super().set_product_last_purchase(order_id)
        purchaseOrderLine = self.env['purchase.order.line']
        if not self.check_access_rights('write', raise_exception=False):
            return
        for product in self:
            currency_purchase_id = product.env.user.company_id.currency_id.id
            if order_id:
                lines = purchaseOrderLine.search([
                    ('order_id', '=', order_id),
                    ('product_id', '=', product.id)], limit=1)
            else:
                lines = purchaseOrderLine.search(
                    [('product_id', '=', product.id),
                     ('state', 'in', ['purchase', 'done'])]).sorted(
                    key=lambda l: l.order_id.date_order, reverse=True)

            if lines:
                # Get most recent Purchase Order Line
                last_line = lines[:1]
                currency_purchase_id = last_line.order_id.currency_id.id
            product.currency_purchase_id = currency_purchase_id
            # Set related product template values
            product.product_tmpl_id.set_product_template_currency_purchase(currency_purchase_id)
        return res

    @api.onchange('type')
    def onchange_product_type(self):
        for product in self:
            if product.type=='service':
                product.invoice_policy = 'order'
            elif product.type=='product':
                product.invoice_policy = 'delivery'


    @api.onchange('name')
    def onchange_product_default_code(self):
        for product in self:
            if product.name:
                product.default_code = product.name
            elif not product.name:
                product.default_code = ''

    @api.model
    def create(self, vals):
        prod = super().create(vals)
        if self.env.user.company_id.country_id.code == 'IT'and prod.seller_ids:
            prod.last_supplier_id = prod.seller_ids[0].name.id
        return prod


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_table(self):
        res = super().open_table()
        if res.get('domain'):
            res['domain'] = "[('type', '=', 'product')]"
        return res
