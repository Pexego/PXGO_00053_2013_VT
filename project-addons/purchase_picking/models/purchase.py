##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from odoo import models, fields, api, _
from odoo.exceptions import except_orm,UserError
from odoo.tools.float_utils import float_is_zero, float_compare


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    picking_created = fields.Boolean('Picking created', compute='is_picking_created')

    date_planned = fields.Datetime(string='Scheduled Date', compute='', store=True, index=True)

    total_no_disc = fields.Float(compute='_get_total', store=True, readonly=True, string='Amount without disc.')

    total_disc = fields.Float(compute='_get_amount_discount', store=True, readonly=True, string='Disc. amount')

    container_ids = fields.Many2many('stock.container', string='Containers', compute='_get_containers')

    @api.multi
    def _get_containers(self):
        for order in self:
            res = []
            for line in order.order_line:
                for move in line.move_ids:
                    if move.state != 'cancel':
                        res.append(move.container_id.id)
            order.container_ids = res

    @api.multi
    @api.depends('order_line.price_subtotal')
    def _get_total(self):
        for order in self:
            for line in order.order_line:
                order.total_no_disc += line.product_qty * line.price_unit

    @api.multi
    @api.depends('order_line.price_subtotal')
    def _get_amount_discount(self):
        for order in self:
            for line in order.order_line:
                order.total_disc += (line.product_qty * line.price_unit) - line.price_subtotal

    @api.multi
    def test_moves_done(self):
        '''PO is done at the delivery side if all the incoming shipments
           are done'''
        for purchase in self:
            for line in purchase.order_line:
                for move in line.move_ids:
                    if move.state != 'done':
                        return False
        return True

    @api.multi
    def is_picking_created(self):
        for order in self:
            order.picking_created = order.picking_ids and True or False

    @api.multi
    def _create_picking(self):
        """
            Se sobreescribe la función para que no se cree el picking.
        """
        if self.env.context.get('bypass_override'):
            return super()._create_picking()
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                void_pick = self.env['stock.picking']
                moves = order.order_line._create_stock_moves(void_pick)
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
        return True

    @api.multi
    def move_lines_create_picking(self):
        self.ensure_one()
        result = self.env['ir.actions.act_window'].for_xml_id('purchase_picking', 'action_receive_move')
        move_lines = self.env['stock.move'].search([('origin', 'like', self.name + '%'),
                                   ('picking_id', '=', False)])
        if len(move_lines) < 1:
            raise except_orm(_('Warning'), _('There is any move line without associated picking'))

        result['context'] = []
        if len(move_lines) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, move_lines.ids)) + "])]"
        else:
            result['domain'] = "[('id','='," + str(move_lines[0].id) + ")]"
        return result

    @api.multi
    def _add_supplier_to_product(self):
        """Update the partner info in the supplier list of the product if the
        supplier is registered for this product."""
        super()._add_supplier_to_product()
        partner = self.partner_id if not self.partner_id.parent_id else \
            self.partner_id.parent_id
        for line in self.order_line:
            if line.price_unit > 0:
                seller = line.product_id._select_seller(
                    partner_id=partner,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and
                    line.order_id.date_order[:10],
                    uom_id=line.product_uom)
                if seller:
                    currency = (
                        partner.property_purchase_currency_id or
                        self.env.user.company_id.currency_id)
                    seller.write({
                        'price': line.price_unit,
                        'currency_id': self.currency_id.id,
                    })

    @api.multi
    def delete_purchase_lines(self):
        for order in self:
            for line in order.order_line:
                if line.select_delete:
                    line.unlink()


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    select_delete = fields.Boolean(' ')

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)

        for move_dict in res:
            move_dict.pop('picking_id', None)
            move_dict.pop('product_uos_qty', None)
            move_dict.pop('product_uos', None)
            move_dict['partner_id'] = self.order_id.partner_id.id
            if self.order_id.partner_ref:
                move_dict['origin'] += ":" + self.order_id.partner_ref

        return res

    @api.multi
    def write(self, vals):
        res = super(PurchaseOrderLine, self).write(vals)
        for line in self:
            if line.move_ids and vals.get('date_planned', False):
                for move in line.move_ids:
                    if move.state not in ['cancel', u'done'] and \
                            not move.container_id:
                        move.date_expected = vals['date_planned']
        return res
