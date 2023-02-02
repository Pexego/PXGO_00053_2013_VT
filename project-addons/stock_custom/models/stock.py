##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos
#    $Carlos Lombardía Rodríguez <carlos@comunitea.com>$
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
from odoo import api, exceptions, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = "priority desc, date desc, id desc"

    internal_notes = fields.Text()
    commercial = fields.Many2one('res.users')
    move_location_id = fields.\
        Many2one('stock.location', related='move_lines.location_id',
                 string='Moves origin location', readonly=True, store=True)
    move_location_dest_id = fields.\
        Many2one('stock.location', related='move_lines.location_dest_id',
                 string='Moves destination location', readonly=True,
                 store=True)

    def action_done(self):
        lot_obj = self.env["stock.production.lot"]
        mov_line_obj = self.env['stock.move.line']
        for picking in self:
            for move in picking.move_lines:
                if move.product_id.tracking != 'none' and \
                        move.state == 'assigned' and not move.quantity_done:
                    for line in move.move_line_ids:
                        line.qty_done = line.product_uom_qty
                if move.product_id.tracking == 'none' and \
                        move.state == 'assigned' and \
                        not move.quantity_done and not picking.block_picking:
                    move.quantity_done = move.product_uom_qty
        res = super().action_done()
        for picking in self:
            if picking.sale_id:
                picking_states = self.env['stock.picking'].search_read([('sale_id', '=', picking.sale_id.id)],['state'])
                if all(picking['state'] in ('done', 'cancel') for picking in picking_states) \
                        and not all(picking['state'] == 'cancel' for picking in picking_states):
                    picking.sale_id.action_done()
        return res

    def check_send_email_base(self, vals):
        return ((vals.get('carrier_tracking_ref', False) and self.carrier_name and not self.carrier_tracking_ref) or
                (vals.get('carrier_name', False) and self.carrier_tracking_ref and not self.carrier_name) or
                (vals.get('carrier_name', False) and vals.get('carrier_tracking_ref',
                                                              False) and not self.carrier_name and not self.carrier_tracking_ref)) and \
               self.partner_id.email

    def check_send_email_extended(self, vals):
        return self.sale_id and self.picking_type_code == 'outgoing'

    def check_send_email(self, vals):
        return self.check_send_email_base(vals) and self.check_send_email_extended(vals)

    def get_email_template(self):
        return self.env.ref('stock_custom.picking_done_template').with_context(lang=self.partner_id.commercial_partner_id.lang)

    @api.multi
    def write(self, vals):
        pickings_to_send = []
        for picking in self:
            if picking.check_send_email(vals):
                pickings_to_send.append(picking)
        result = super().write(vals)
        if pickings_to_send:
            for picking in pickings_to_send:
                # We need to do this after the write, otherwise the email template won't get well some  picking values
                picking_template = picking.get_email_template()
                picking_template.send_mail(picking.id)
        return result

    @api.multi
    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        self.filtered(lambda picking: picking.picking_type_code == 'outgoing' and picking.location_id.usage=='internal' and picking.state == 'confirmed') \
                .mapped('move_lines')._action_assign()
        return res

    @api.onchange('partner_id')
    def change_partner(self):
        if (
            (self.state in ('assigned', 'done', 'cancel') or self.block_picking)
            and
            not (self.state == 'assigned' and self.not_sync)
        ):
            raise exceptions.Warning(_("You can not modify the shipping address"))


class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'

    sale_line = fields.Many2one('sale.order.line', store=True)
    sale_price_unit = fields.Float(store=True)
    sale_discount = fields.Float(store=True)
    sale_tax_description = fields.Char(store=True)
    sale_price_subtotal = fields.Monetary(store=True)
    sale_price_tax = fields.Float(store=True)
    sale_price_total = fields.Monetary(store=True)
    date_expected = fields.Datetime(related='move_id.date_expected',
                                    string="Date Expected")

    @api.depends('sale_line', 'sale_line.currency_id', 'sale_line.tax_id')
    def _compute_sale_order_line_fields(self):
        return super()._compute_sale_order_line_fields()


class StockMove(models.Model):
    _inherit = "stock.move"

    _order = 'date_expected asc, id'

    real_stock = fields.Float(compute='_compute_real_stock')
    available_stock = fields.Float(compute="_compute_available_stock")
    user_id = fields.Many2one('res.users', compute='_compute_responsible')
    lots_text = fields.Text('Serials', help="Value must be separated by commas")
    sale_id = fields.Many2one('sale.order', related='sale_line_id.order_id',
                              readonly=True)
    date_reliability = fields.Selection([
        ('1.high', 'High'),
        ('2.medium', 'Medium'),
        ('3.low', 'Low'),
        ], readonly=False,compute='_compute_dates')

    date_done = fields.Datetime(related='picking_id.date_done', store=True)
    date_expected_conf = fields.Boolean(related='container_id.conf', store=False)

    def _compute_is_initial_demand_editable(self):
        super()._compute_is_initial_demand_editable()
        for move in self:
            if move.picking_id.state == 'draft' or (move.picking_id.state in ('confirmed', 'assigned') and move.picking_id.picking_type_id.code == 'incoming'):
                move.is_initial_demand_editable = True

    def _compute_responsible(self):
        for move in self:
            responsible = None
            if move.picking_id:
                responsible = move.picking_id.commercial.id
            elif move.sale_id:
                responsible = move.sale_id.user_id.id
            elif move.origin:
                responsible = move.env['sale.order'].search(
                    [('name', '=', move.origin)]).user_id.id
            move.user_id = responsible

    def _compute_available_stock(self):
        for move in self:
            move.available_stock = move.product_id.virtual_stock_conservative

    def _compute_real_stock(self):
        for move in self:
            move.real_stock = move.product_id.qty_available

    def _compute_dates(self):
        for move in self:
            if move.picking_id:
                move.date_reliability="1.high"
            elif move.container_id:
                move.date_reliability="2.medium"
            else:
                move.date_reliability="3.low"

    @api.multi
    def _action_done(self):
        res = super()._action_done()
        stock_loc = self.env.ref("stock.stock_location_stock")
        for move in self:
            if (move.location_id.usage in ('supplier', 'production')) and \
                    (move.product_id.cost_method == 'fifo'):
                move.product_id.product_tmpl_id.recalculate_standard_price_2()
            if move.location_dest_id == stock_loc:
                domain = [('state', 'in', ['confirmed',
                                           'partially_available']),
                          ('picking_type_code', '=', 'outgoing'),
                          ('product_id', '=', move.product_id.id)]
                confirmed_ids = self.\
                    search(domain, limit=None,
                           order="has_reservations,sequence,date_expected,id")
                if confirmed_ids:
                    confirmed_ids._action_assign()
            if move.location_dest_id.name == 'Tránsito Italia':
                # TODO: revisar y permitir aplicar en otras circustancias para el futuro
                self._push_apply()
        return res

    def _get_price_unit(self):
        res = super()._get_price_unit()
        if not res:
            res = self.product_id.standard_price_2
        return res

    def action_do_unreserve(self):
        for move in self:
            if not move.mapped('move_line_ids'):
                move.state = 'confirmed'
        return self._do_unreserve()

    def action_force_assign(self):
        return self._force_assign()

    @api.multi
    def write(self,vals):
        if len(vals) > 1 and 'product_uom_qty' in vals and vals['product_uom_qty'] == self.product_uom_qty:
            # This is the case when the user modifies the price of the
            # sale order line, in this case product_uom_qty is also write
            # and that put the state "partially_available" on the reserve
            del vals['product_uom_qty']
        res = super(StockMove, self).write(vals)
        for move in self:
            if move.purchase_line_id and move.product_id.date_first_incoming_reliability!='1.received' and (vals.get('date_expected') or vals.get('state') =='cancel' or vals.get('picking_id')==False):
                move.product_id._compute_date_first_incoming()
            if vals.get('date_expected') and move.purchase_line_id != False and move.state not in ['cancel','done'] and move.location_dest_id.usage=='internal':
                move.product_id.with_delay().update_product()
        return res

    @api.multi
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        if vals.get('date_expected') and vals.get('purchase_line_id') and vals.get('state') not in ['cancel',
                                                                                                   'done'] and self.env['stock.location'].browse(vals.get('location_dest_id')).usage == 'internal':
                self.env['product.product'].browse(vals.get('product_id')).with_delay(eta=60).update_product()
        return res

    @api.multi
    def _compute_parent_partner(self):
        for move in self:
            move.parent_partner = move.sale_line_id.order_id.partner_id if move.sale_line_id else move.partner_id
    parent_partner = fields.Many2one('res.partner', compute="_compute_parent_partner", string="Partner")

    purchase_order_id = fields.Many2one('purchase.order', related='purchase_line_id.order_id')


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        new_picking, pick_type_id = super()._create_returns()
        pick_type_obj = self.env["stock.picking.type"].browse(pick_type_id)
        if pick_type_obj.code == "incoming":
            pick_obj = self.env["stock.picking"].browse(new_picking)
            location_stock = self.env.ref('stock.stock_location_stock')
            if pick_obj.move_lines and pick_obj.location_dest_id.id == location_stock.id:
                pick_obj.location_dest_id = pick_obj.move_lines[0].warehouse_id.wh_input_stock_loc_id.id
            for move in pick_obj.move_lines:
                if move.warehouse_id.lot_stock_id == move.location_dest_id:
                    move.location_dest_id = \
                        move.warehouse_id.wh_input_stock_loc_id.id
        return new_picking, pick_type_id


class StockReservation(models.Model):
    _inherit = 'stock.reservation'

    next_reception_date = fields.Datetime(compute='_compute_next_reception_date')

    def _compute_next_reception_date(self):
        for reservation in self:
            moves = self.env['stock.move'].search(
                [('product_id', '=', reservation.product_id.id), ('purchase_line_id', '!=', False),
                 ('state', 'not in', ['cancel', 'done']), ('location_dest_id.usage', 'like', 'internal')]).sorted(
                key=lambda m: m.date_expected and m.date_reliability)
            reservation.next_reception_date = moves[0].date_expected if moves else False


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        compute='_compute_partner_id',
        help='The last customer in possession of the product')
    lot_notes = fields.Text('Notes')
    order_id= fields.Many2one('sale.order',string='Order',compute='_compute_partner_id')
    picking_id = fields.Many2one('stock.picking',string='Picking',compute='_compute_partner_id')
    def _compute_partner_id(self):
        pass
        for lot in self:
            move_line = self.env['stock.move.line'].search(
                [('lot_id', '=', lot.id)], order="id desc", limit=1)
            if move_line:
                lot.partner_id = \
                    move_line.picking_id.partner_id.commercial_partner_id
                lot.order_id=move_line.move_id.sale_line_id.order_id
                lot.picking_id =move_line.picking_id
            else:
                lot.partner_id = False


class StockLandedCost(models.Model):

    _inherit = 'stock.landed.cost'

    def button_validate(self):
        res = super().button_validate()
        valuation_lines = self.valuation_adjustment_lines.\
            filtered(lambda line: line.move_id)
        valuation_lines.mapped('move_id.product_id.product_tmpl_id').\
            recalculate_standard_price_2()
        return res


class PushedFlow(models.Model):
    _inherit = "stock.location.path"

    apply_at_finish = fields.Boolean(string='Apply at finish',
                                     help='Apply the rule when move is done')

    def _apply(self, move):
        if not self.apply_at_finish or (self.apply_at_finish and move.state == 'done'):
            super()._apply(move)
