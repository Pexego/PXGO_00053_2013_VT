# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class MrpProductProduce(models.TransientModel):

    _inherit = 'mrp.product.produce'

    final_lot = fields.Boolean('final lot', compute='_get_final_lot')
    lot_id = fields.Many2one('stock.production.lot', 'Lot', compute='_get_lot')

    @api.one
    @api.depends('final_lot')
    def _get_lot(self):
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id'))
        if production.final_prod_lot:
            self.lot_id = production.final_prod_lot

    @api.multi
    def do_produce(self):
        production_id = self.env.context.get('active_id', False)
        assert production_id, \
            "Production Id should be specified in context as a Active ID."
        production = self.env['mrp.production'].browse(production_id)
        if not self.lot_id and self.final_lot:
            for line in self.produce_line_ids:
                if line.final_lot and line.lot_id:
                    self.lot_id = self.env['stock.production.lot'].create(
                        {'name': line.lot_id.name,
                         'product_id': production.product_id.id}).id

        production.create_out_picking()
        super(MrpProductProduce, self).do_produce()
        return True

    @api.one
    @api.depends('produce_line_ids')
    def _get_final_lot(self):
        final_lot = False
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id'))
        for line in self.produce_line_ids:
            if line.final_lot:
                final_lot = True
        if production.final_prod_lot:
            final_lot = True
        self.final_lot = final_lot
