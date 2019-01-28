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
from odoo.exceptions import except_orm
from odoo.tools.float_utils import float_is_zero, float_compare


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    picking_created = fields.Boolean('Picking created', compute='is_picking_created')

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
    def _prepare_stock_moves(self, picking):
        self.ensure_one()
        import ipdb
        ipdb.set_trace()
        res = super(PurchaseOrder, self)._prepare_stock_moves(picking)

        for move_dict in res:
            move_dict.pop('picking_id', None)
            move_dict.pop('product_uos_qty', None)
            move_dict.pop('product_uos', None)
            move_dict['partner_id'] = self.partner_id.id
            if self.partner_ref:
                move_dict['origin'] += ":" + self.partner_ref

        return res

    @api.multi
    def _create_picking(self):
        """
            Se sobreescribe la función para que no se cree el picking.
        """
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                void_pick = self.env['stock.picking']
                moves = order.order_line._create_stock_moves(void_pick)
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
        return True

    # Esta función es muy extraña
    @api.multi
    def move_lines_create_picking(self):
        self.ensure_one()
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        moves = self.env['stock.move']

        result = act_obj.read()[0]

        move_lines = moves.search([('origin', 'like', self.name + '%'),
                                   ('picking_id', '=', False)])
        if len(move_lines) < 1:
            raise except_orm(_('Warning'), _('There is any move line without associated picking'))

        result['context'] = []
        if len(move_lines) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, move_lines)) + "])]"
        else:
            result['domain'] = "[('id','='," + str(move_lines[0]) + ")]"
        return result


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

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
