# © 2014 Pexego Sistemas Informáticos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, exceptions, _


class ProductOutletWizard(models.TransientModel):
    _name = 'product.outlet.wizard'

    @api.model
    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse']. \
            search([('company_id', '=', company_id)])
        if not warehouse_ids:
            return False
        return warehouse_ids[0].id

    @api.model
    def _get_default_location(self):
        company_id = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse']. \
            search([('company_id', '=', company_id)])
        if not warehouse_ids:
            return False
        return warehouse_ids[0].lot_rma_id.id

    qty = fields.Float('Quantity')
    product_id = fields.Many2one('product.product', 'Product',
                                 default=lambda self:
                                 self.env.context.get('active_id', False))
    categ_id = fields.Selection(selection='_get_outlet_categories',
                                string='category')
    state = fields.Selection([('first', 'First'), ('last', 'Last')],
                             default='first')
    ean13 = fields.Char('EAN13', size=13)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse',
                                   required=True,
                                   default=_get_default_warehouse)
    location_orig_id = fields.Many2one("stock.location", "Orig. location",
                                       required=True,
                                       default=_get_default_location)
    percent = fields.Float(string="Percent",
                           help="This percent will be used when a product moves to an outlet category")

    @api.onchange('categ_id')
    def onchange_percent(self):
        if self.state == 'last':
            self.percent = self.env['product.category'].browse(self.categ_id).percent

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        if self.warehouse_id:
            product = self.env['product.product']. \
                with_context(warehouse=self.warehouse_id.id). \
                browse(self.env.context['active_id'])
            self.qty = product.qty_available
        else:
            self.qty = 0.0

    @api.model
    def _get_outlet_categories(self):
        res = []
        outlet_categ_id = self.env. \
            ref('product_outlet.product_category_outlet')
        for categ in outlet_categ_id.child_id:
            res.append((categ.id, categ.name))
        return res

    def make_move(self):
        outlet_categ_id = \
            self.env.ref('product_outlet.product_category_outlet')
        loss_location = self.env.\
            ref('product_outlet.stock_location_outlet_changes')
        stock_location = self.location_orig_id
        move_obj = self.env['stock.move']
        categ_obj = self.env['product.category']
        outlet_tag = self.env.ref('product_outlet.tag_outlet')
        product = self.with_context(
            warehouse=self.warehouse_id.id,
            location=self.location_orig_id.id).product_id
        if self.state == 'first':
            self.qty = product.qty_available
            self.state = 'last'
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.outlet.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }

        if self.qty > product.qty_available:
            raise exceptions.except_orm(
                _('Quantity error'),
                _('the amount entered is greater than the quantity '
                  'available in stock.'))
        if product.categ_id == outlet_categ_id or \
                product.categ_id.parent_id == outlet_categ_id:
            raise exceptions.except_orm(
                _('product error'),
                _('This product is already in outlet category.'))

        # crear nuevo producto
        outlet_product = self.env['product.product'].search(
            [('normal_product_id', '=', product.id),
             ('categ_id', '=', int(self.categ_id))])

        if not outlet_product:
            outlet_product = self.env['product.product'].search(
                [('default_code', '=', product.default_code + categ_obj.browse(int(self.categ_id)).name),
                 ('categ_id', '=', int(self.categ_id))])
        if not outlet_product:
            new_product = product.copy(
                {'categ_id': int(self.categ_id),
                 'name': product.name +
                         categ_obj.browse(int(self.categ_id)).name,
                 'default_code': product.default_code +
                                 categ_obj.browse(int(self.categ_id)).name,
                 'image_medium': product.image_medium,
                 'barcode': self.ean13 or False})
            categ = self.env['product.category'].browse(int(self.categ_id))
            tag = self.env['product.tag'].search([('name', '=',
                                                   categ.name)])
            if not tag:
                outlet_tag = self.env.ref('product_outlet.tag_outlet')
                tag = self.env['product.tag'].create(
                    {'name': categ.name, 'parent_id': outlet_tag.id})
            new_product.write({'tag_ids': [(4, tag.id)]})
            new_product.normal_product_id = self.product_id
        else:
            outlet_product.normal_product_id = product.id
            new_product = outlet_product
        new_product.sale_ok = True

        move_in = move_obj.create({'product_id': new_product.id,
                                   'product_uom_qty': self.qty,
                                   'location_id': loss_location.id,
                                   'location_dest_id':
                                       self.warehouse_id.wh_input_stock_loc_id.id,
                                   'product_uom': new_product.uom_id.id,
                                   'picking_type_id':
                                       self.warehouse_id.in_type_id.id,
                                   'partner_id':
                                       self.env.user.company_id.partner_id.id,
                                   'name': "OUTLET"})
        move_out = move_obj.create({'product_id': product.id,
                                    'product_uom_qty': self.qty,
                                    'location_id': stock_location.id,
                                    'location_dest_id': loss_location.id,
                                    'product_uom': product.uom_id.id,
                                    'picking_type_id':
                                        self.warehouse_id.out_type_id.id,
                                    'move_dest_id': move_in.id,
                                    'partner_id':
                                        self.env.user.company_id.partner_id.id,
                                    'name': "OUTLET"})

        move_out._action_confirm()
        move_out._action_assign()
        move_out.picking_id.not_sync = True
        move_out.picking_id.odoo_management = True
        move_in._action_confirm()
        return {'type': 'ir.actions.act_window_close'}
