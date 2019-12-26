from odoo import fields, models,api


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def _compute_date_first_incoming(self):
        for product in self:
            moves = self.env['stock.move'].search([('product_id','=',product.id),('picking_id','!=',False),('picking_id.date_done','!=',False),('purchase_line_id','!=',False)])
            if moves:
                pickings=self.env['stock.picking'].search([('id','in',moves.mapped('picking_id.id'))], order='date_done asc',limit=1)
                product.date_first_incoming=pickings.date_done
            else:
                moves = self.env['stock.move'].search([('product_id', '=', product.id),('purchase_line_id','!=',False)]).sorted(key=lambda m:m.date_expected and m.date_reliability)
                if moves:
                    product.date_first_incoming = moves[0].date_expected

    date_first_incoming =fields.Date(formats=['%Y-%m-%d %H:%M:%S'], compute=_compute_date_first_incoming)


