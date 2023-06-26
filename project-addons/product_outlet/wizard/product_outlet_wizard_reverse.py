from odoo import models, fields, api, exceptions, _


class ProductOutletReverseWizard(models.TransientModel):

    _name = 'product.outlet.reverse.wizard'

    @api.model
    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse']. \
            search([('company_id', '=', company_id)])
        if not warehouse_ids:
            return False
        return warehouse_ids[0].id

    @api.model
    def _get_product_categ(self):
        product = self.env['product.product'].browse(self.env.context.get('active_id', False))
        if product:
            return product.categ_id.name

    qty = fields.Float('Quantity')
    product_id = fields.Many2one('product.product', 'Product',
                                 default=lambda self:
                                 self.env.context.get('active_id', False))
    categ_name = fields.Char('Category', readonly=True, default=_get_product_categ)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse',
                                   required=True,
                                   default=_get_default_warehouse)

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        if self.warehouse_id:
            product = self.env['product.product']. \
                with_context(warehouse=self.warehouse_id.id). \
                browse(self.env.context['active_id'])
            self.qty = product.qty_available
        else:
            self.qty = 0.0

    def make_reverse_move(self):

        loss_location = self.env.ref('product_outlet.stock_location_outlet_changes')
        stock_location = self.warehouse_id.lot_stock_id
        move_obj = self.env['stock.move']
        product = self.with_context(
            warehouse=self.warehouse_id.id,
            location=stock_location.id).product_id

        if self.qty > product.qty_available:
            raise exceptions.except_orm(
                _('Quantity error'),
                _('The amount entered is greater than the quantity '
                  'available in stock.'))

        move_in = move_obj.create({'product_id': product.normal_product_id.id,
                                   'product_uom_qty': self.qty,
                                   'location_id': loss_location.id,
                                   'location_dest_id':
                                       self.warehouse_id.wh_input_stock_loc_id.id,
                                   'product_uom': product.normal_product_id.uom_id.id,
                                   'picking_type_id':
                                       self.warehouse_id.in_type_id.id,
                                   'partner_id':
                                       self.env.user.company_id.partner_id.id,
                                   'name': "REVERSE OUTLET"})
        move_out = move_obj.create({'product_id': product.id,
                                    'product_uom_qty': self.qty,
                                    'location_id': stock_location.id,
                                    'location_dest_id': loss_location.id,
                                    'product_uom': product.uom_id.id,
                                    'picking_type_id':
                                        self.warehouse_id.out_type_id.id,
                                    'move_dest_ids': [(6, 0, [move_in.id])],
                                    'partner_id':
                                        self.env.user.company_id.partner_id.id,
                                    'name': "REVERSE OUTLET"})

        move_out._action_confirm()
        move_out._action_assign()
        move_in._action_confirm()
        return {'type': 'ir.actions.act_window_close'}
