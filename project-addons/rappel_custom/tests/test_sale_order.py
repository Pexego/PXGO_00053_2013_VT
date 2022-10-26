from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    post_install = True
    at_install = True

    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.so_model = self.env['sale.order']
        self.sol_model = self.env['sale.order.line']
        self.res_partner_model = self.env['res.partner']
        self.product_model = self.env['product.product']

    def test_change_no_rappel_from_false_to_true(self):
        # arrange
        partner_id = self.res_partner_model.create(dict(name="Pedro"))
        product_id = self.product_model.create({'default_code': "Camera",
                                                'name': "Camera"})
        so_vals = {'partner_id': partner_id.id,
                   'no_rappel': False,
                   'order_line': [
                       (0, 0, {
                           'product_id': product_id.id,
                           'product_uom_qty': 1.0,
                           'product_uom': 1,
                           'price_unit': 10.0
                       }),
                       (0, 0, {
                           'product_id': product_id.id,
                           'product_uom_qty': 2.0,
                           'product_uom': 1,
                           'price_unit': 10.0,
                       }),
                   ]
                   }
        order = self.so_model.create(so_vals)

        # act
        order.no_rappel = True
        order.onchange_no_rappel()

        # assert
        self.assertTrue(order.order_line[0].no_rappel)
        self.assertTrue(order.order_line[1].no_rappel)
