# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api

STATES = [('in_progress', 'In Progress'),
          ('in_action', 'In Action'),
          ('finalized', 'Finalized'),
          ('exception', 'Exception'),
          ('cancelled', 'Cancelled')]


class ProductStockUnsafety(models.Model):
    _name = 'product.stock.unsafety'
    _description = 'Products that have stock under minimum'
    _order = 'id desc'

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 readonly=True,
                                 required=True)
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint',
                                    'Replenishement Rule',
                                    readonly=True,
                                    required=True,
                                    ondelete='cascade',
                                    help='The replenishement rule that '
                                    'launch this under minimum alert.')
    supplier_id = fields.Many2one('res.partner',
                                  'Supplier',
                                  readonly=True)
    remaining_days_sale = fields.Float(
        related='product_id.remaining_days_sale',
        string='Remaining Days of Sale',
        readonly=True)
    real_stock = fields.Float(related='product_id.qty_available',
                              string='Real Stock', readonly=True,
                              help='Quantity in stock')
    virtual_stock = fields.Float(
        related='product_id.virtual_stock_conservative',
        string='Virtual Stock Conservative',
        readonly=True,
        help='Real stock - outgoings ')
    brand_id = fields.Many2one("product.brand", "Brand", readonly=True)
    virtual_available = fields.Float(
        related='product_id.virtual_available',
        string='Quantity available',
        readonly=True,
        help='Real stock + incomings - '
        'outgongs')
    last_sixty_days_sales = fields.\
        Float(related='product_id.last_sixty_days_sales',
              readonly=True, digits=(16, 2),
              string="Sales in last 60 days with stock")
    biggest_sale_qty = fields.Float(related='product_id.biggest_sale_qty',
                                    digits=(16, 2), readonly=True,
                                    string="Biggest sale qty")
    biggest_sale_id = fields.Many2one("sale.order",
                                      related="product_id.biggest_sale_id",
                                      readonly=True, string="Biggest order")
    purchase_id = fields.Many2one('purchase.order',
                                  'Purchase', readonly=True)
    product_qty = fields.Float('Qty ordered')
    responsible = fields.Many2one('res.users',
                                  'Responsible', readonly=True)
    state = fields.Selection(STATES, 'State', readonly=True)
    date = fields.Date('Date', readonly=True, default=fields.Date.today)
    name = fields.Char('Reason', size=64, readonly=True)
    incoming_qty = fields.Float(related='product_id.incoming_qty',
                                string='Incoming qty.',
                                readonly=True,
                                help='Quantity pending to recive')
    minimum_proposal = fields.Float(
        'Min. Proposal', readonly=True,
        help='Quantity necessary to reach the minimum days of purchase')
    product_type = fields.Selection(
        [("manufacture", "To manufacture"),
         ("buy", "To buy")], "Product type",
        required=True)
    bom_id = fields.Many2one("mrp.bom", "Bill of material", readonly=True)
    production_id = fields.Many2one("mrp.production", "Production",
                                    readonly=True)
    min_days_id = fields.Many2one(
        'minimum.day', 'Stock Minimum Days', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('minimum_proposal', False):
            vals['product_qty'] = vals['minimum_proposal']
        return super().create(vals)

    def cancel(self):
        return self.write({'state': 'cancelled'})
