from odoo.tests.common import SavepointCase


class TestSaleOrder(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        cls.partner_id = cls.env['res.partner'].create(dict(name="Peter"))
        cls.product_id = cls.env['product.product'].create({'name': "Test",
                                                            'default_code': "Test",
                                                            'special_shipping_costs': True
                                                            })
        cls.product_id2 = cls.env['product.product'].create({'name': "Test1",
                                                             'default_code': "Test1",
                                                             'special_shipping_costs': False
                                                             })
        cls.partner_id = cls.env['res.partner'].create(dict(name="Peter"))
        cls.uom_id = cls.env['product.uom'].search([('name', '=', 'Unit(s)')])[0]
        cls.pricelist = cls.env['product.pricelist'].search([('name', '=', 'Public Pricelist')])[0]
        cls.order = cls.env['sale.order'].create({'partner_id': cls.partner_id.id,
                                                  'pricelist_id': cls.pricelist.id,
                                                  'order_line': [
                                                      (0, 0, {
                                                          'name': cls.product_id.name,
                                                          'product_id': cls.product_id2.id,
                                                          'product_uom_qty': 1.0,
                                                          'product_uom': cls.uom_id.id,
                                                          'price_unit': 100.0
                                                      })]
                                                  })

    def test_verifies_that_special_shipping_costs_is_false_due_to_there_are_no_products_with_special_shipping_costs_checked(
        self):
        # act
        self.env['sale.order.line'].create({'name': self.product_id.name,
                                             'product_id': self.product_id2.id,
                                             'product_uom_qty': 1.0,
                                             'product_uom': self.uom_id.id,
                                             'price_unit': 100.0,
                                             'order_id': self.order.id
                                             })

        # assert
        self.assertFalse(self.order.is_special_shipping_costs)

    def test_verifies_that_special_shipping_costs_is_true_due_to_there_are_products_with_special_shipping_costs_checked(
        self):
        # act
        self.env['sale.order.line'].create({'name': self.product_id.name,
                                             'product_id': self.product_id.id,
                                             'product_uom_qty': 1.0,
                                             'product_uom': self.uom_id.id,
                                             'price_unit': 100.0,
                                             'order_id': self.order.id
                                             })

        # assert
        self.assertTrue(self.order.is_special_shipping_costs)
