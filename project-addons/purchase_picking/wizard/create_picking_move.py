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


from openerp import models, fields, api


class create_picking_move(models.TransientModel):

    _name = "picking.from.moves.wizard"

    date_picking = fields.Datetime('Date planned', required=True)


    def _view_picking(self):
        action = self.env.ref('stock.action_picking_tree').read()[0]
        pick_ids = self.env.context.get('picking_ids', [])
        #override the context to get rid of the default filtering on picking type
        action['context'] = {}
        #choose the view_mode accordingly
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
        moves = self.env['stock.move'].browse(context['active_ids'])
        picking_types = {}
        all_moves = []
        partner_id = moves[0].partner_id.id
        same_partner = True

        # se recorren los movimientos para agruparlos por tipo
        for move in moves:
            if move.state != u'draft' or move.picking_id:
                continue
            if partner_id != move.partner_id.id:
                same_partner = False
            if move.picking_type_id.id not in picking_types.keys():
                picking_types[move.picking_type_id.id] = []
            picking_types[move.picking_type_id.id].append(move)
            move.date_expected = self.date_picking
            all_moves.append(move.id)
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
                'date': self.date_picking
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
