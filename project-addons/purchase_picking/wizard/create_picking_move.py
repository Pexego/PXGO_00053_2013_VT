# -*- coding: utf-8 -*-
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


from openerp import models, fields, api, exceptions, _

class move_details(models.TransientModel):

    _name = 'picking.wizard.move.details'

    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Quantity')
    move_id = fields.Many2one('stock.move', 'Move')
    wizard_id = fields.Many2one('picking.from.moves.wizard', 'wizard')


class create_picking_move(models.TransientModel):

    @api.model
    def _get_lines(self):
        wiz_lines = []
        move_ids = self.env.context.get('active_ids', [])
        for move in self.env['stock.move'].browse(move_ids):
            if move.state != u'draft' or move.picking_id:
                continue
            wiz_lines.append({'product_id': move.product_id.id,
                              'qty': move.product_uom_qty,
                              'move_id': move.id})
        return wiz_lines

    _name = "picking.from.moves.wizard"

    date_picking = fields.Datetime('Date planned', required=True)
    move_detail_ids = fields.One2many('picking.wizard.move.details',
                                      'wizard_id', 'lines', default=_get_lines)

    def _view_picking(self):
        action = self.env.ref('stock.action_picking_tree').read()[0]
        pick_ids = self.env.context.get('picking_ids', [])
        # override the context to get rid of the default filtering on picking type
        action['context'] = {}
        # choose the view_mode accordingly
        if len(pick_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        else:
            res =  self.env.ref('stock.view_picking_form').id
            action['views'] = [(res, 'form')]
            action['res_id'] = pick_ids and pick_ids[0].id or False
        return action

    @api.multi
    def action_create_picking(self):
        context = self.env.context
        if not context.get('active_ids', False):
            return

        picking_types = {}
        all_moves = []
        partner_id = self.move_detail_ids[0].move_id.partner_id.id
        same_partner = True
        # se recorren los movimientos para agruparlos por tipo
        for move in self.move_detail_ids:

            if partner_id != move.move_id.partner_id.id:
                same_partner = False
            if move.move_id.picking_type_id.id not in picking_types.keys():
                picking_types[move.move_id.picking_type_id.id] = []
            if move.qty != move.move_id.product_uom_qty:
                if move.qty > move.move_id.product_uom_qty:
                    raise exceptions.except_orm(_('Quantity error'), _('The quantity is greater than the original.'))
                new_move = move.move_id.copy({'product_uom_qty': move.qty})
                new_move.purchase_line_id = move.move_id.purchase_line_id
                picking_types[move.move_id.picking_type_id.id].append(new_move)
                move.move_id.product_uom_qty = move.move_id.product_uom_qty - move.qty
            else:
                picking_types[move.move_id.picking_type_id.id].append(move.move_id)
                move.move_id.date_expected = self.date_picking
                all_moves.append(move.move_id.id)
        if not same_partner:
            partner_id = self.env.ref('purchase_picking.partner_multisupplier').id
        picking_ids = []

        # se crea un albarán por cada tipo
        for pick_type in picking_types.keys():
            moves_type = picking_types[pick_type]
            picking_vals = {
                'partner_id': partner_id,
                'picking_type_id': pick_type,
                'move_lines': [(6, 0, [x.id for x in moves_type])],
                'origin': ''.join([x.purchase_line_id.order_id.name + ", "
                           for x in moves_type]),
                'min_date': self.date_picking
            }
            picking_vals['origin'] = picking_vals['origin'][:-2]
            picking_ids.append(self.env['stock.picking'].create(picking_vals))
        # TODO: Se vuelven a buscar todos los movimientos para tener un
        #       recordset y poder llamar a las funciones, tal vez se pueda
        #       conseguir sin volver a buscar 2 veces.
        all_moves = self.env['stock.move'].browse(all_moves)
        all_moves = all_moves.action_confirm()

        all_moves = self.env['stock.move'].browse(all_moves)

        all_moves.force_assign()
        context2 = dict(context)
        context2['picking_ids'] = picking_ids
        return self.with_context(context2)._view_picking()
