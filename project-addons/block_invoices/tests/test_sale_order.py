from odoo.tests.common import SavepointCase
from odoo.exceptions import Warning
from mock import patch


class TestSaleOrder(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        cls.so_model = cls.env['sale.order']
        cls.so_line_model = cls.env['sale.order.line']
        cls.res_partner_model = cls.env['res.partner']
        cls.product_model = cls.env['product.product']
        cls.product_uom_model = cls.env['product.uom']
        cls.pricelist_model = cls.env['product.pricelist']
        cls.partner_id = cls.res_partner_model.create(dict(name="Peter"))
        cls.uom_id = cls.product_uom_model.search([('name', '=', 'Unit(s)')])[0]
        cls.pricelist = cls.pricelist_model.search([('name', '=', 'Public Pricelist')])[0]
        cls.pricelist_pvi = cls.pricelist_model.search([('name', 'like', 'PVIIberia')])[0]

        cls.product_id = cls.product_model.create({'name': "Test",
                                                   'default_code': "Test",
                                                   'standard_price_2_inc':1
                                                   })

        cls.product_id_2 = cls.product_model.create({'name': "Test2",
                                                     'default_code': "Test2",
                                                     'exclude_margin': True,
                                                     'standard_price_2_inc':1})
        so_vals = {
            'partner_id': cls.partner_id.id,
            'pricelist_id': cls.pricelist.id,
            'order_line': [
                (0, 0, {
                    'name': cls.product_id.name,
                    'product_id': cls.product_id.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0,
                    'deposit': True
                }),
                (0, 0, {
                    'name': cls.product_id_2.name,
                    'product_id': cls.product_id_2.id,
                    'product_uom_qty': 2.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 10.0,
                }),
                (0, 0, {
                    'name': cls.product_id.name,
                    'product_id': cls.product_id_2.id,
                    'product_uom_qty': 2.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 10.0,
                    'promotion_line': True
                }),
            ]
        }
        cls.order = cls.so_model.create(so_vals)

        so_vals_no_lines = {
            'partner_id': cls.partner_id.id,
            'pricelist_id': cls.pricelist.id,
        }
        cls.order_no_lines = cls.so_model.create(so_vals_no_lines)
        cls.team_magreb = cls.env['crm.team'].search([('name','=','Magreb')])


    def test_check_order_exceptions_when_amount_total_is_greater_than_magreb_limit_and_order_team_name_is_magreb(self):
        # arrange
        self.order.team_id = self.team_magreb.id
        self.env['ir.config_parameter'].sudo().set_param('magreb.limit.without.block',10)
        # act and assert
        with self.assertRaises(Warning):
            self.order.check_order_exceptions()

    def test_check_order_exceptions_when_amount_total_is_greater_than_magreb_limit_and_partner_team_name_is_magreb(self):
        # arrange
        self.order.partner_id.team_id = self.team_magreb.id
        self.env['ir.config_parameter'].sudo().set_param('magreb.limit.without.block',10)
        # act and assert
        with self.assertRaises(Warning):
            self.order.check_order_exceptions()

    def test_check_order_exceptions_when_amount_total_is_less_than_magreb_limit_and_order_team_name_is_not_magreb_and_pricelist_is_not_pvi(self):
        # arrange
        self.env['ir.config_parameter'].sudo().set_param('margin.lock.limit',-200)
        # act
        with patch(
            'odoo.addons.block_invoices.models.sale_order.SaleOrder.get_margin_adjustment') as get_margin_adjustment_mock:
            self.order.check_order_exceptions()
        # assert
        self.assertEqual(get_margin_adjustment_mock.call_count, 1)

    def test_check_order_exceptions_when_amount_total_is_less_than_magreb_limit_and_order_team_name_is_not_magreb_and_pricelist_is_pvi(self):
        # arrange
        self.env['ir.config_parameter'].sudo().set_param('margin.lock.limit',-200)
        self.order.pricelist_id = self.pricelist_pvi
        # act
        with patch(
            'odoo.addons.block_invoices.models.sale_order.SaleOrder.get_margin_adjustment') as get_margin_adjustment_mock:
            self.order.check_order_exceptions()
        # assert
        self.assertEqual(get_margin_adjustment_mock.call_count, 0)


    def test_check_order_exceptions_when_pricelist_is_not_pvi_and_margin_below_limits(self):
        # arrange
        self.env['ir.config_parameter'].sudo().set_param('margin.lock.limit',20)
        # act and assert
        with patch(
            'odoo.addons.block_invoices.models.sale_order.SaleOrder.get_margin_adjustment') as get_margin_adjustment_mock:
            with self.assertRaises(Warning):
                self.order.check_order_exceptions()
            self.assertEqual(get_margin_adjustment_mock.call_count, 1)

    def test_get_margin_adjustment_when_all_lines_are_excluded_because_they_are_promotions_or_deposits_or_product_has_exclude_margin_check(
        self):
        # act
        margin = self.order.get_margin_adjustment()

        # assert
        self.assertEqual(margin, 0)

    def test_get_margin_adjustment_when_there_are_no_lines(self):
        # act
        margin = self.order_no_lines.get_margin_adjustment()

        # assert
        self.assertEqual(margin, 0)

    def test_get_margin_adjustment_when_there_are_lines_included_on_margin_with_price_equals_to_0(self):
        # arrange
        self.order.order_line[0].write({'deposit':False, 'price_unit':0})
        # act
        margin = self.order.get_margin_adjustment()

        # assert
        self.assertEqual(margin, 0)

    def test_get_margin_adjustment_when_there_are_lines_included_on_margin_with_price_less_than_0(self):
        # arrange
        self.order.order_line[0].write({'deposit': False, 'price_unit': -5})
        # act
        margin = self.order.get_margin_adjustment()

        # assert
        self.assertEqual(margin, -5)

    def test_get_margin_adjustment_when_there_are_lines_included_on_margin_with_price_greater_than_0_and_sale_price_is_greater_than_purchase(self):
        # arrange
        self.order.order_line[0].write({'deposit': False,'margin_rappel':150})
        # act
        margin = self.order.get_margin_adjustment()

        # assert
        self.assertEqual(margin, 150)

    def test_get_margin_adjustment_when_there_are_lines_included_on_margin_with_price_greater_than_0_and_purchase_price_is_greater_than_sale(self):
        # arrange
        line = self.order.order_line[0]
        line.write({'deposit': False, 'margin_rappel': 150})
        line.product_id.standard_price_2_inc = 120

        # act
        margin = self.order.get_margin_adjustment()

        # assert
        self.assertEqual(margin, (150 * 100) / 120)

