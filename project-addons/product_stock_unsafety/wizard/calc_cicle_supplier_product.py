# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class CalcCicleSupplierProduct(models.TransientModel):

    _name = "calc.cicle.supplier.product"

    supplier_id = fields.Many2one(
        "res.partner", "Supplier", domain=[('supplier', '=', True)])
    order_cycle = fields.Integer("Order Cicle")

    def set_cicle_supplier_product(self):
        """Set the cicle of a product depends of the first supplier"""
        vals = {'order_cycle': self.order_cycle}
        products_data = self.env['purchase.order.line'].read_group(
            [('invoiced', '=', True),
             ('order_id.partner_id', '=', self.supplier_id.id)],
            ['product_id'], ['product_id'])
        for product_data in products_data:
            purchase = self.env['purchase.order.line'].search(
                [('product_id', '=', product_data['product_id'][0]),
                 ('invoiced', '=', True)],
                order='id desc', limit=1)
            if self.supplier_id.id == purchase.order_id.partner_id.id:
                product = purchase.product_id
                product.write(vals)
