# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    final_prod_lot = fields.Many2one('stock.production.lot', 'Final lot')
    type_ids = fields.Many2many(
        'mrp.customize.type', 'mrp_customizations_rel',
        'production_id', 'customization_id', 'Type')
    sale_line_id = fields.Many2one('sale.order.line', 'order line')
    sale_id = fields.Many2one(related="sale_line_id.order_id",
                              relation="sale.order", string="Sale",
                              readonly=True)
    production_name = fields.Char("Production ref", readonly=True)
    picking_out = fields.Many2one(
        'stock.picking', "Out picking", readonly=True)
    picking_in = fields.Many2one(
        'stock.picking', "In picking", readonly=True)

    def action_assign(self):
        res = super().action_assign()
        for production in self:
            for move in production.move_raw_ids:
                if move.state == 'confirmed':
                    reserv_dict = {
                        'date_validity': False,
                        'name': "{} ({})".format(production.name, move.name),
                        'mrp_id': production.id,
                        'move_id': move.id
                    }
                    reservation = self.env['stock.reservation'].create(
                        reserv_dict)
                    reservation.reserve()
        return res

    @api.multi
    def create_out_picking(self):
        picking = self.env['stock.picking']
        # Create out picking
        pick_out = picking.create({'partner_id': self.company_id.partner_id.id,
                                   'picking_type_id': self.env.ref('stock.picking_type_out').id,
                                   'location_id': self.move_raw_ids and self.move_raw_ids[0].location_id.id,
                                   'location_dest_id': self.move_raw_ids and self.move_raw_ids[0].location_dest_id.id,
                                   'origin': self.name})
        # Update reference out picking
        self.picking_out = pick_out.id
        self.move_raw_ids.write({'picking_id': pick_out.id})
        self.move_raw_ids.mapped('move_line_ids').write({'picking_id': pick_out.id})


class MrpBomLine(models.Model):

    _inherit = 'mrp.bom.line'

    final_lot = fields.Boolean('Same final product lot')


class MrpProductProduceLine(models.TransientModel):

    _inherit = 'mrp.product.produce.line'

    final_lot = fields.Boolean('final lot', compute='_get_final_lot')

    @api.one
    @api.depends('product_id')
    def _get_final_lot(self):
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        bom_line = []
        if not production.final_prod_lot:
            bom_line = self.env['mrp.bom.line'].search(
                [('bom_id', '=', production.bom_id.id),
                 ('final_lot', '=', True),
                 ('product_id', '=', self.product_id.id)])
        if bom_line:
            self.final_lot = True
        else:
            self.final_lot = False

# TODO: Migrar
# ~ class StockMoveConsume(models.TransientModel):

    # ~ _inherit = 'stock.move.consume'

    # ~ final_lot = fields.Boolean('final lot')

    # ~ @api.model
    # ~ def default_get(self, fields):
        # ~ res = super(StockMoveConsume, self).default_get(fields)
        # ~ move = self.env['stock.move'].browse(self.env.context['active_id'])
        # ~ if 'final_lot' in fields:
            # ~ bom_line = self.env['mrp.bom.line'].search(
                # ~ [('bom_id', '=', move.raw_material_production_id.bom_id.id),
                 # ~ ('final_lot', '=', True),
                 # ~ ('product_id', '=', move.product_id.id)])
            # ~ res.update({'final_lot': bom_line and bom_line.final_lot or False})
        # ~ return res

    # ~ @api.one
    # ~ def do_move_consume(self):
        # ~ move = self.env['stock.move'].browse(self.env.context['active_id'])
        # ~ if self.final_lot:
            # ~ production_lot = self.env['stock.production.lot'].create(
                # ~ {'name': self.restrict_lot_id.name,
                 # ~ 'product_id': move.raw_material_production_id.product_id.id})
            # ~ move.raw_material_production_id.final_prod_lot = production_lot
        # ~ return super(StockMoveConsume, self).do_move_consume()
