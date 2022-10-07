from odoo.tests.common import SavepointCase


class TestPromotionsRulesActions(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super(TestPromotionsRulesActions, cls).setUpClass()
        cls.so_model = cls.env['sale.order']
        cls.so_line_model = cls.env['sale.order.line']
        cls.rules_model = cls.env['promos.rules.actions']
        cls.res_partner_model = cls.env['res.partner']
        cls.product_tag_model = cls.env['product.tag']
        cls.tax_model = cls.env['account.tax']
        cls.product_tmpl_model = cls.env['product.template']
        cls.product_model = cls.env['product.product']
        cls.product_uom_model = cls.env['product.uom']
        cls.pricelist_model = cls.env['product.pricelist']
        cls.promos_rules = cls.env["promos.rules"]
        cls.partner_id = cls.res_partner_model.create(dict(name="Peter"))
        cls.product_tag = cls.product_tag_model.create({'name': 'Prueba'})
        cls.uom_id = cls.product_uom_model.search([('name', '=', 'Unit(s)')])[0]
        cls.pricelist = cls.pricelist_model.search([('name', '=', 'Public Pricelist')])[0]

        cls.product_id = cls.product_model.create({'name': "Test",
                                                     'default_code': "Test",
                                                     'tag_ids': [(6, 0, [cls.product_tag.id])]})

        cls.product_id_2 = cls.product_model.create({'name': "Test2",
                                                       'default_code': "Test2"})
        so_vals = {
            'partner_id': cls.partner_id.id,
            'pricelist_id': cls.pricelist.id,
            'order_line': [
                (0, 0, {
                    'name': cls.product_id.name,
                    'product_id': cls.product_id.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                }),
                (0, 0, {
                    'name': cls.product_id_2.name,
                    'product_id': cls.product_id_2.id,
                    'product_uom_qty': 2.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 10.0,
                }),
            ]
        }
        cls.order = cls.so_model.create(so_vals)
        cls.promo = cls.promos_rules.create({
            'sequence': 0,
            'name': 'Promo Test',
            'line_description': 'Promo T1'
        })
        cls.order2 = cls.so_model.create({'partner_id': cls.partner_id.id})
        cls.rule = cls.rules_model.create(
            {'sequence': 0, 'action_type': 'disc_per_product', 'promotion': cls.promo.id})
        cls.rule2 = cls.rules_model.create(
            {'sequence': 0, 'action_type': 'fix_price_per_product', 'promotion': cls.promo.id})

    def test_get_qty_by_tag_when_a_parameter_is_empty(self):
        # Act
        qty = self.rules_model.get_qty_by_tag(False, self.order2)
        qty1 = self.rules_model.get_qty_by_tag(self.product_tag.name, False)
        qty2 = self.rules_model.get_qty_by_tag(False, self.so_model)
        qty3 = self.rules_model.get_qty_by_tag(self.product_tag_model, False)
        qty4 = self.rules_model.get_qty_by_tag(self.product_tag_model, self.so_model)

        # Assert
        self.assertEquals(qty, 0)
        self.assertEquals(qty1, 0)
        self.assertEquals(qty2, 0)
        self.assertEquals(qty3, 0)
        self.assertEquals(qty4, 0)

    def test_get_qty_by_tag_when_an_order_has_no_lines(self):
        # Act
        qty = self.rules_model.get_qty_by_tag(self.product_tag.name, self.order2)

        # Assert
        self.assertEquals(qty, 0)

    def test_get_qty_by_tag_when_an_order_has_lines(self):
        # Act
        qty = self.rules_model.get_qty_by_tag(self.product_tag.name, self.order)

        # Assert
        self.assertEquals(qty, 1)

    def test_get_new_lines_when_a_parameter_is_empty(self):
        # Act
        lines = self.rules_model.get_new_lines([], 0)
        lines1 = self.rules_model.get_new_lines([], 2)

        # Assert
        self.assertEquals(lines, [])
        self.assertEquals(lines1, [])

    def test_get_new_lines_when_there_are_less_products_exp_lines_than_products_tag_with_different_prices(self):
        # Act
        lines = self.rules_model.get_new_lines([[1, 2]], 2)
        # Assert
        self.assertEquals(lines, [[1, 1, 2]])

    def test_get_new_lines_when_there_are_more_products_exp_lines_than_products_tag_with_different_prices(self):
        # Act
        lines = self.rules_model.get_new_lines([[1, 2], [2, 3], [2, 4]], 2)
        # Assert
        self.assertEquals(lines, [[1, 1, 2], [1, 2, 3]])

    def test_get_new_lines_when_there_are_equal_products_exp_lines_than_products_tag_with_different_prices(self):
        # Act
        lines = self.rules_model.get_new_lines([[1, 2], [2, 3]], 2)
        # Assert
        self.assertEquals(lines, [[1, 1, 2], [1, 2, 3]])

    def test_get_new_lines_when_there_are_equal_products_exp_lines_than_products_tag_with_same_price(self):
        # Act
        lines = self.rules_model.get_new_lines([[2, 2], [2, 2]], 2)
        # Assert
        self.assertEquals(lines, [[2, 2, 2]])

    def test_get_match_products_when_there_is_at_least_one_with_qty_equals_to_one(self):
        line = self.order.order_line[0]
        # Act
        lines = self.rules_model.get_match_products(self.order,
                                                    "line.product_id.default_code == '%s'" % self.product_id.name)
        # Assert
        self.assertEquals(lines, [[line.price_subtotal / line.product_uom_qty, line.product_id.default_code]])

    def test_get_match_products_when_there_is_at_least_one_with_qty_greater_than_one(self):
        line = self.order.order_line[0]
        line2 = self.order.order_line[1]
        # Act
        lines = self.rules_model.get_match_products(self.order,
                                                    "line.product_id.default_code in %s" % [self.product_id.name,
                                                                                            self.product_id_2.name])
        # Assert
        self.assertEquals(lines, [[line2.price_subtotal / line2.product_uom_qty, line2.product_id.default_code],
                                  [line2.price_subtotal / line2.product_uom_qty, line2.product_id.default_code],
                                  [line.price_subtotal / line.product_uom_qty, line.product_id.default_code]])

    def test_get_match_products_when_there_are_no_mathing_products(self):
        # Act
        lines = self.rules_model.get_match_products(self.order, "line.product_id.default_code == '%s'" % 'test3')
        # Assert
        self.assertEquals(lines, [])

    def test_get_match_products_when_there_are_no_lines_in_order(self):
        # Act
        lines = self.rules_model.get_match_products(self.order2, "line.product_id.default_code == '%s'" % 'test3')
        # Assert
        self.assertEquals(lines, [])

    def test_create_lines_per_product_when_there_are_no_new_lines(self):
        self.rules_model.create_lines_per_product(self.order2, [], "5")
        self.assertEquals(self.order2.order_line, self.so_line_model)

    def test_create_lines_per_product_when_there_are_new_lines(self):
        # Act
        """[[qty, price, product], [qty, price, product], ...]"""
        self.rule.create_lines_per_product(self.order, [[1, 25, "Prueba1"]], "5")
        # Assert
        self.assertEquals(len(self.order.order_line), 3)
        self.assertEquals(self.order.order_line[2].price_unit, 5)
        self.assertEquals(self.order.order_line[2].name, 'Promo Promo T1 - Prueba1')

    def test_action_disc_per_product_when_promo_applies_to_this_order(self):
        # Arrange
        self.rule.product_code = "['Prueba','^Test2']"
        self.rule.arguments = "10"
        # Act
        self.rule.action_disc_per_product(self.order)
        # Assert
        self.assertEquals(len(self.order.order_line), 3)
        self.assertEquals(self.order.order_line[2].price_unit, -1)
        self.assertEquals(self.order.order_line[2].product_uom_qty, 1)
        self.assertEquals(self.order.order_line[2].name, 'Promo Promo T1 - Test2')

    def test_action_disc_per_product_when_promo_no_applies_to_this_order(self):
        # Arrange
        self.rule.product_code = "['Prueba','^Test2-(W-Z)']"
        self.rule.arguments = "10"
        # Act
        self.rule.action_disc_per_product(self.order)
        # Assert
        self.assertEquals(len(self.order.order_line), 2)

    def test_action_disc_per_product_when_promo_applies_to_this_order_and_have_an_optional_qty_parameter(self):
        # Arrange
        self.rule.product_code = "['Prueba','^Test2', 5]"
        self.rule.arguments = "10"
        # Act
        self.rule.action_disc_per_product(self.order)
        # Assert
        self.assertEquals(self.order.order_line[2].price_unit, -1)
        self.assertEquals(self.order.order_line[2].product_uom_qty, 2)
        self.assertEquals(self.order.order_line[2].name, 'Promo Promo T1 - Test2')

    def test_action_fix_price_per_product_when_promo_applies_to_this_order(self):
        # Arrange
        self.rule2.product_code = "'Prueba'"
        self.rule2.arguments = "{'Test2':5, 'EZ-TY2':25}"
        # Act
        self.rule2.action_fix_price_per_product(self.order)
        # Assert
        self.assertEquals(len(self.order.order_line), 3)
        self.assertEquals(self.order.order_line[2].price_unit, -5)
        self.assertEquals(self.order.order_line[2].product_uom_qty, 1)
        self.assertEquals(self.order.order_line[2].name, 'Promo Promo T1 - Test2')

    def test_action_fix_price_per_product_when_promo_no_applies_to_this_order(self):
        # Arrange
        self.rule2.product_code = "'Prueba'"
        self.rule2.arguments = "{'EZ-C1T':20, 'EZ-TY2':25}"
        # Act
        self.rule2.action_fix_price_per_product(self.order)
        # Assert
        self.assertEquals(len(self.order.order_line), 2)
