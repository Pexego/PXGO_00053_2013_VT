# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('reserve', 'Reserved'),
        ('sale', 'Sales Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ])

    @api.multi
    @api.depends('state',
                 'order_line.reservation_ids',
                 'order_line.is_stock_reservable')
    def _compute_stock_reservation(self):
        for sale in self:
            has_stock_reservation = False
            is_stock_reservable = False
            for line in sale.order_line:
                if line.reservation_ids:
                    has_stock_reservation = True
                if line.is_stock_reservable:
                    is_stock_reservable = True
            if sale.state not in ('draft', 'sent', 'reserve'):
                is_stock_reservable = False
            sale.is_stock_reservable = is_stock_reservable
            sale.has_stock_reservation = has_stock_reservation

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.state == 'reserve':
            res.order_reserve()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        print(vals)
        if vals.get('order_line', False):
            lines = [line[1] for line in vals['order_line']
                     if line[2] and line[2].get('product_uom_qty') and line[0] == 1]  # 1 = write, 0 = create
            if lines:
                self.env['sale.order.line'].browse(lines).\
                    filtered(lambda r: r.product_id and r.product_id.type != 'service'
                                       and r.promotion_line is not True).\
                    stock_reserve()
        return res

    def order_reserve(self):
        self.write({'state': 'reserve'})
        lines = self.mapped('order_line').filtered(
            lambda r: r.product_id and r.product_id.type != 'service' and r.promotion_line is not True)
        lines.stock_reserve()
        return True

    def open_stock_reservation(self):
        self.ensure_one()
        action = self.env.ref('stock_reserve.action_stock_reservation_tree').read()[0]
        action['domain'] = [('sale_id', 'in', self.ids)]
        action['context'] = {'search_default_draft': 1,
                             'search_default_reserved': 1,
                             'search_default_waiting': 1,
                             'search_default_partially_available': 1,
                            }
        return action


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    # unique_js_id = fields.Char('', size=64, copy=False)
    # temp_unique_js_id = fields.Char('', size=64, copy=False)
    qty_reserved = fields.Float(readonly=True,
                                related='product_id.reservation_count',
                                digits=dp.get_precision('Product Unit \
                                                  of Measure'))
    hide_reserve_buttons = fields.Boolean("Hide reserve buttons",
                                          compute='_compute_hide_reserve_buttons',
                                          readonly=True)

    @api.multi
    @api.depends('state', 'product_id', 'reservation_ids')
    def _compute_is_stock_reservation(self):
        for line in self:
            reservable = False
            if not (line.state not in ('draft', 'reserve') or line._get_procure_method() == 'make_to_order' or not line.product_id or line.product_id.type == 'service'):
                reservable = True
            line.is_stock_reservable = reservable

    def _test_block_on_reserve(self, vals):
        super()._test_block_on_reserve(vals)
        return False

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.product_id and res.product_id.type != 'service' \
                and res.promotion_line is not True and res.order_id.state == 'reserve':
            res.stock_reserve()
        return res

    def stock_reserve(self):
        days_release_reserve = self.env['ir.config_parameter'].sudo().get_param('days_to_release_reserve_stock')
        now = datetime.now()
        date_validity = (now + relativedelta(days=int(days_release_reserve))).strftime("%Y-%m-%d")

        if self.env.context.get('later', False):
            return True

        for line in self:
            if line.order_id.state in ('draft', 'sent', 'progress', 'done',
                                       'manual'):
                continue
            if not line.is_stock_reservable:
                continue
            if line.reservation_ids:
                for reserve in line.reservation_ids:
                    reserve.reassign()
            else:
                vals = line._prepare_stock_reservation(date_validity=date_validity)
                vals['user_id'] = line.order_id.user_id.id
                reservation = self.env['stock.reservation'].create(vals)
                reservation.reserve()
                if line.product_id.is_pack:
                    pack_reservation = self.env['stock.reservation'].search([('sale_line_id', '=', line.id)])
                    pack_reservation.write({'sale_line_id': line.id})
                    pack_reservation.write({'origin': line.order_id.name})
                else:
                    reservation.write({'sale_line_id': line.id})
                    reservation.write({'origin': line.order_id.name})
        return True

    @api.multi
    @api.depends('order_id.partner_id')
    def _compute_hide_reserve_buttons(self):
        for line in self:
            if line.order_id.partner_id.user_id.id == line.env.user.id \
                    or line.env.user.has_group('base.group_system'):
                line.hide_reserve_buttons = False
            else:
                line.hide_reserve_buttons = True
