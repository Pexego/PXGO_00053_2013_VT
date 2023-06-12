from odoo import fields, models, api, _, exceptions


class EquivalentProductsWizard(models.TransientModel):
    _name = 'equivalent.products.wizard'
    _description = 'Wizard for change products in claim.'

    product_id = fields.Many2one('product.product', 'Product selected')
    line_id = fields.Many2one('claim.line', 'Line')

    product_ids = fields.Many2many(comodel_name='product.product', readonly=True)

    def default_get(self, fields):
        res = super(EquivalentProductsWizard, self).default_get(fields)
        if self.env.context.get('claim_line'):
            claim_line_id = self.env.context['claim_line']
            res['product_id'] = claim_line_id.product_id.id
            products = self.env['product.product']
            if claim_line_id.product_id.normal_product_id:
                products += claim_line_id.product_id.normal_product_id + claim_line_id.product_id.normal_product_id.outlet_product_ids
            else:
                products += claim_line_id.product_id + claim_line_id.product_id.outlet_product_ids
            res['product_ids'] = [(6, 0, products.ids)]
        return res

    @api.onchange("product_id")
    def onchange_product_id(self):
        products = self.env['product.product']
        if self.product_id.normal_product_id:
            products += self.product_id.normal_product_id + self.product_id.normal_product_id.outlet_product_ids
        else:
            products += self.product_id + self.product_id.outlet_product_ids
        self.product_ids = [(6, 0, products.ids)]

    @api.multi
    def select_product(self):
        self.line_id.equivalent_product_id = self.product_id

    @api.multi
    def delete_product(self):
        moves = self.line_id.move_ids.filtered(lambda m: m.picking_code == self.env.ref(
            'stock.picking_type_out').code and m.location_dest_id.usage in ['supplier', 'customer']
                                                 and m.location_id.id != self.env.ref(
            'crm_rma_advance_location.stock_location_rma').id)
        if moves and any([x.state == 'cancel' for x in moves]):
            raise exceptions.UserError(_("There are open pickings that contain this product"))
        else:
            self.line_id.equivalent_product_id = None
            self.env.user.notify_info(title=_("Product deleted"), message=_("Check the status of the line"))
