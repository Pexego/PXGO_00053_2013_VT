##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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


class StockReserve(models.Model):

    _inherit = 'stock.reservation'

    mrp_id = fields.Many2one('mrp.production', 'Production')


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.one
    def _get_if_productions(self):
        with_prods = False
        for line in self.move_lines:
            if line.procurement_id and line.procurement_id.sale_line_id \
                    and line.procurement_id.sale_line_id.mrp_production_ids:
                with_prods = True
                break
        self.with_productions = with_prods

    with_productions = fields.Boolean("With productions", readonly=True,
                                      compute='_get_if_productions')

    #TODO: Migrar
    # ~ @api.multi
    # ~ def write(self, vals):
        # ~ res = super(StockPicking, self).write(vals)
        # ~ production_obj = self.env['mrp.production']
        # ~ if self.origin and 'MO' in self.origin and vals.get('date_done', False) and self.state == 'done':
            # ~ mrp_production = production_obj.search([('name', '=', self.origin)])
            # ~ if mrp_production.picking_out.id == self.id:
                # ~ # Create in picking
                # ~ pick_in = self.create({'partner_id': self.partner_id.id,
                                       # ~ 'picking_type_id': self.env.ref('stock.picking_type_in').id,
                                       # ~ 'origin': self.origin})
                # ~ # Update reference in_picking and the state
                # ~ mrp_production.write({'state': 'in_production',
                                      # ~ 'picking_in': pick_in.id})
                # ~ cost_moves = sum(self.move_lines.mapped('price_unit'))
                # ~ for move in production_obj.search([('name', '=', self.origin)]).move_created_ids:
                    # ~ move.write({'price_unit': cost_moves,
                                # ~ 'picking_id': pick_in.id})
                # ~ pick_in.action_assign()
            # ~ elif mrp_production.picking_in.id == self.id:
                # ~ mrp_production.action_production_end()
        # ~ return res
