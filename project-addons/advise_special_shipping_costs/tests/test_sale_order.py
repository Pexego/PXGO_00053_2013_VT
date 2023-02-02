from odoo.tests.common import SavepointCase


class TestSaleOrder(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        cls.partner_id = cls.env['res.partner'].create(dict(name="Peter"))
        cls.special_costs_product = cls.env['product.product'].create({
            'name': "Test",
            'default_code': "Test",
            'special_shipping_costs': True
        })
        cls.not_special_costs_product = cls.env['product.product'].create({
            'name': "Test1",
            'default_code': "Test1",
            'special_shipping_costs': False
        })
        cls.uom_id = cls.env['product.uom'].search([('name', '=', 'Unit(s)')])[0]
        cls.pricelist = cls.env['product.pricelist'].search([('name', '=', 'Public Pricelist')])[0]
        cls.shipping_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_id.id,
            'pricelist_id': cls.pricelist.id,
            'delivery_type': 'shipping',
            'order_line': [
                (0, 0, {
                    'name': cls.not_special_costs_product.name,
                    'product_id': cls.not_special_costs_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                })]
        })
        cls.carrier_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_id.id,
            'pricelist_id': cls.pricelist.id,
            'delivery_type': 'carrier',
            'order_line': [
                (0, 0, {
                    'name': cls.not_special_costs_product.name,
                    'product_id': cls.not_special_costs_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                })]
        })
        cls.installations_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_id.id,
            'pricelist_id': cls.pricelist.id,
            'delivery_type': 'installations',
            'order_line': [
                (0, 0, {
                    'name': cls.not_special_costs_product.name,
                    'product_id': cls.not_special_costs_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                })]
        })

    def test_verifies_that_special_shipping_costs_is_false_and_its_transporter_is_not_changed_in_shipping_order_due_to_there_are_no_products_with_special_shipping_costs_checked(
        self):
        # act
        self.env['sale.order.line'].create({'name': self.not_special_costs_product.name,
                                            'product_id': self.not_special_costs_product.id,
                                            'product_uom_qty': 1.0,
                                            'product_uom': self.uom_id.id,
                                            'price_unit': 100.0,
                                            'order_id': self.shipping_order.id
                                            })

        # assert
        self.assertFalse(self.shipping_order.is_special_shipping_costs)
        self.assertFalse(self.shipping_order.transporter_id)

    def test_verifies_that_special_shipping_costs_is_true_and_its_transporter_is_changed_in_shipping_order_due_to_there_are_products_with_special_shipping_costs_checked(
        self):
        # act
        self.env['sale.order.line'].create({'name': self.special_costs_product.name,
                                            'product_id': self.special_costs_product.id,
                                            'product_uom_qty': 1.0,
                                            'product_uom': self.uom_id.id,
                                            'price_unit': 100.0,
                                            'order_id': self.shipping_order.id
                                            })

        # assert
        self.assertTrue(self.shipping_order.is_special_shipping_costs)
        self.assertEquals(self.shipping_order.transporter_id,
                          self.env.ref('advise_special_shipping_costs.palletized_shipping_transporter'))

    def test_verifies_that_special_shipping_costs_is_false_and_its_transporter_is_not_changed_in_carrier_order_when_adding_products(
        self):
        # act
        self.env['sale.order.line'].create({'name': self.not_special_costs_product.name,
                                            'product_id': self.not_special_costs_product.id,
                                            'product_uom_qty': 1.0,
                                            'product_uom': self.uom_id.id,
                                            'price_unit': 100.0,
                                            'order_id': self.carrier_order.id
                                            })

        # assert
        self.assertFalse(self.carrier_order.is_special_shipping_costs)
        self.assertFalse(self.carrier_order.transporter_id)

        # act
        self.env['sale.order.line'].create({'name': self.special_costs_product.name,
                                            'product_id': self.special_costs_product.id,
                                            'product_uom_qty': 1.0,
                                            'product_uom': self.uom_id.id,
                                            'price_unit': 100.0,
                                            'order_id': self.carrier_order.id
                                            })

        # assert
        self.assertFalse(self.carrier_order.is_special_shipping_costs)
        self.assertFalse(self.carrier_order.transporter_id)

    def test_verifies_that_special_shipping_costs_is_false_and_its_transporter_is_not_changed_in_installations_order_when_adding_products(
        self):
        # act
        self.env['sale.order.line'].create({'name': self.not_special_costs_product.name,
                                            'product_id': self.not_special_costs_product.id,
                                            'product_uom_qty': 1.0,
                                            'product_uom': self.uom_id.id,
                                            'price_unit': 100.0,
                                            'order_id': self.installations_order.id
                                            })

        # assert
        self.assertFalse(self.installations_order.is_special_shipping_costs)
        self.assertFalse(self.installations_order.transporter_id)

        # act
        self.env['sale.order.line'].create({'name': self.special_costs_product.name,
                                            'product_id': self.special_costs_product.id,
                                            'product_uom_qty': 1.0,
                                            'product_uom': self.uom_id.id,
                                            'price_unit': 100.0,
                                            'order_id': self.installations_order.id
                                            })

        # assert
        self.assertFalse(self.installations_order.is_special_shipping_costs)
        self.assertFalse(self.installations_order.transporter_id)
