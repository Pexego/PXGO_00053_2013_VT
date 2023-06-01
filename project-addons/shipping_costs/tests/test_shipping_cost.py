from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError, UserError


class TestShippingCost(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_format = cls.env['postal.code.format'].create({
            'name': 'Test format',
            'regex': r'\A(\d{5})$',
            'postal_code_sample': '12345'
        })
        cls.country = cls.env['res.country'].create({
            'name': 'Test Country',
            'postal_code_format_id': cls.postal_code_format.id
        })
        cls.partner = cls.env['res.partner'].create({
            'company_type': 'person',
            'name': 'Test partner',
            'country_id': cls.country.id
        })
        cls.good_service = cls.env['transportation.service'].create({'name': 'Good service test'})
        cls.bad_service = cls.env['transportation.service'].create({'name': 'Bad service test'})
        cls.good_transporter = cls.env['transportation.transporter'].create({
            'name': 'Good transporter',
            'partner_id': cls.partner.id,
            'service_ids': [(4, cls.good_service.id)]
        })
        cls.bad_transporter = cls.env['transportation.transporter'].create({
            'name': 'BAd transporter',
            'partner_id': cls.partner.id
        })
        cls.supplement_good_service = cls.env['shipping.cost.supplement'].create({
            'service_id': cls.good_service.id,
            'added_percentage': 10.0
        })
        cls.supplement_bad_service = cls.env['shipping.cost.supplement'].create({
            'service_id': cls.bad_service.id,
            'added_percentage': 5.0
        })
        cls.good_zone = cls.env['shipping.zone'].create({
            'name': 'Good zone',
            'transporter_id': cls.good_transporter.id,
            'country_id': cls.country.id,
            'postal_code_ids': [
                (0, 0, {'first_code': '00012', 'last_code': '00099'}),
                (0, 0, {'first_code': '01012', 'last_code': '01099'})
            ]
        })
        cls.bad_zone = cls.env['shipping.zone'].create({
            'name': 'Bad zone',
            'transporter_id': cls.bad_transporter.id,
            'country_id': cls.country.id
        })
        cls.one_pallet_fee = cls.env['shipping.cost.fee'].create({
            'type': 'pallet',
            'max_qty': 1,
            'price': 10.0
        })
        cls.five_pallet_fee = cls.env['shipping.cost.fee'].create({
            'type': 'pallet',
            'max_qty': 5,
            'price': 30.0
        })
        cls.weight_50_fee = cls.env['shipping.cost.fee'].create({
            'type': 'total_weight',
            'max_qty': 50.0,
            'price': 15.0
        })
        cls.weight_100_fee = cls.env['shipping.cost.fee'].create({
            'type': 'total_weight',
            'max_qty': 100.0,
            'price': 20.0
        })
        cls.shipping_cost = cls.env['shipping.cost'].create({
            'cost_name': 'Test shipping cost',
            'fee_ids': [
                (4, cls.one_pallet_fee.id),
                (4, cls.five_pallet_fee.id),
                (4, cls.weight_50_fee.id),
                (4, cls.weight_100_fee.id)
            ],
            'volume': 5.0,
            'is_active': True,
            'transporter_id': cls.good_transporter.id,
            'supplement_ids': [(4, cls.supplement_good_service.id)],
            'shipping_zone_id': cls.good_zone.id
        })

    def test_shipping_cost_created_with_services_that_are_not_from_the_transporter_raises_exception(self):
        with self.assertRaisesRegex(
            ValidationError,
            'Error!:: Services must be offered by the transporter selected.'
        ):
            self.env['shipping.cost'].with_context({'lang': 'en'}).create({
                'cost_name': 'Error shipping cost',
                'is_active': True,
                'transporter_id': self.bad_transporter.id,
                'supplement_ids': [(4, self.supplement_good_service.id)]
            })

    def test_shipping_cost_created_with_shipping_zone_that_is_not_from_the_transporter_raises_exception(self):
        with self.assertRaisesRegex(
            ValidationError,
            'Error!:: Shipping zone assigned is not for the transporter selected.'
        ):
            self.env['shipping.cost'].with_context({'lang': 'en'}).create({
                'cost_name': 'Error shipping cost',
                'is_active': True,
                'transporter_id': self.bad_transporter.id,
                'shipping_zone_id': self.good_zone.id
            })

    def test_shipping_cost_updated_with_services_that_are_not_from_the_transporter_raises_exception(self):
        with self.assertRaisesRegex(
            ValidationError,
            'Error!:: Services must be offered by the transporter selected.'
        ):
            error_shipping_cost = self.env['shipping.cost'].create({
                'cost_name': 'Error shipping cost',
                'is_active': True,
                'transporter_id': self.good_transporter.id,
                'supplement_ids': [(4, self.supplement_good_service.id)]
            })
            error_shipping_cost.with_context({'lang': 'en'}).write(
                {'supplement_ids': [(4, self.supplement_bad_service.id)]}
            )

    def test_shipping_cost_updated_with_shipping_zone_that_is_not_from_the_transporter_raises_exception(self):
        with self.assertRaisesRegex(
            ValidationError,
            'Error!:: Shipping zone assigned is not for the transporter selected.'
        ):
            error_shipping_cost = self.env['shipping.cost'].create({
                'cost_name': 'Error shipping cost',
                'is_active': True,
                'transporter_id': self.good_transporter.id,
                'shipping_zone_id': self.good_zone.id
            })
            error_shipping_cost.with_context({'lang': 'en'}).write(
                {'shipping_zone_id': self.bad_zone.id}
            )

    def test_shipping_cost_updated_with_transporter_incorrect_raises_exception(self):
        with self.assertRaisesRegex(
            ValidationError,
            'Error!:: Shipping zone assigned is not for the transporter selected.'
        ):
            self.shipping_cost.with_context({'lang': 'en'}).write({'transporter_id': self.bad_transporter.id})

    def test_get_fee_price_by_weight(self):
        expected_fee = 15
        shipping_weight = 10
        returned_fee = self.shipping_cost.get_fee_price_by_weight(shipping_weight)
        self.assertEqual(expected_fee, returned_fee)

    def test_get_fee_price_by_pallet(self):
        expected_fee = 10
        pallet_number = 1
        returned_fee = self.shipping_cost.get_fee_price_by_pallet(pallet_number)
        self.assertEqual(expected_fee, returned_fee)


class TestSaleOrderShippingCost(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_format = cls.env['postal.code.format'].create({
            'name': 'Test format',
            'regex': r'\A(\d{5})$',
            'postal_code_sample': '12345'
        })
        cls.country = cls.env['res.country'].create({
            'name': 'Test Country',
            'postal_code_format_id': cls.postal_code_format.id
        })
        cls.partner = cls.env['res.partner'].create({
            'company_type': 'person',
            'name': 'Test partner',
            'country_id': cls.country.id
        })

        cls.special_costs_product = cls.env['product.product'].create({
            'name': "Test special cost product",
            'default_code': "Test special cost product",
            'special_shipping_costs': True,
            'weight': 10,
            'volume': 1
        })
        cls.not_special_costs_product = cls.env['product.product'].create({
            'name': "Test no special product",
            'default_code': "Test no special product",
            'special_shipping_costs': False,
            'weight': 10,
            'volume': 1
        })
        cls.uom_id = cls.env['product.uom'].search([('name', '=', 'Unit(s)')])[0]
        cls.pricelist = cls.env['product.pricelist'].search([('name', '=', 'Public Pricelist')])[0]
        cls.special_shipping_cost_sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'delivery_type': 'shipping',
            'order_line': [
                (0, 0, {
                    'name': cls.not_special_costs_product.name,
                    'product_id': cls.not_special_costs_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                }),
                (0, 0, {
                    'name': cls.special_costs_product.name,
                    'product_id': cls.special_costs_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                })]
        })

        cls.good_service = cls.env['transportation.service'].create({'name': 'Good service test'})
        cls.bad_service = cls.env['transportation.service'].create({'name': 'Bad service test'})
        cls.good_transporter = cls.env['transportation.transporter'].create({
            'name': 'Good transporter',
            'partner_id': cls.partner.id,
            'fuel': 10.0,
            'service_ids': [(4, cls.good_service.id)]
        })
        cls.bad_transporter = cls.env['transportation.transporter'].create({
            'name': 'Bad transporter',
            'partner_id': cls.partner.id
        })
        cls.supplement_good_service = cls.env['shipping.cost.supplement'].create({
            'service_id': cls.good_service.id,
            'added_percentage': 10.0
        })
        cls.supplement_bad_service = cls.env['shipping.cost.supplement'].create({
            'service_id': cls.bad_service.id,
            'added_percentage': 5.0
        })
        cls.good_zone = cls.env['shipping.zone'].create({
            'name': 'Good zone',
            'transporter_id': cls.good_transporter.id,
            'country_id': cls.country.id,
            'postal_code_ids': [
                (0, 0, {'first_code': '00012', 'last_code': '00099'}),
                (0, 0, {'first_code': '01012', 'last_code': '01099'})
            ]
        })
        cls.one_pallet_fee = cls.env['shipping.cost.fee'].create({
            'type': 'pallet',
            'max_qty': 1,
            'price': 10.0
        })
        cls.five_pallet_fee = cls.env['shipping.cost.fee'].create({
            'type': 'pallet',
            'max_qty': 5,
            'price': 30.0
        })
        cls.weight_50_fee = cls.env['shipping.cost.fee'].create({
            'type': 'total_weight',
            'max_qty': 50.0,
            'price': 15.0
        })
        cls.weight_100_fee = cls.env['shipping.cost.fee'].create({
            'type': 'total_weight',
            'max_qty': 100.0,
            'price': 20.0
        })
        cls.shipping_cost = cls.env['shipping.cost'].create({
            'cost_name': 'Test shipping cost',
            'fee_ids': [
                (4, cls.one_pallet_fee.id),
                (4, cls.five_pallet_fee.id),
                (4, cls.weight_50_fee.id),
                (4, cls.weight_100_fee.id)
            ],
            'volume': 5.0,
            'transporter_id': cls.good_transporter.id,
            'supplement_ids': [(4, cls.supplement_good_service.id)],
            'shipping_zone_id': cls.good_zone.id
        })

        cls.sale_order_shipping_cost = cls.env['sale.order.shipping.cost'].create({
            'sale_order_id': cls.special_shipping_cost_sale_order.id,
            'shipping_cost_id': cls.shipping_cost.id
        })

    def test_calculates_shipping_costs_correctly(self):
        pallet_prices_expected = [12.1]
        weight_prices_expected = [18.15]

        pallet_result = self.sale_order_shipping_cost.calculate_shipping_cost(
            1,
            10,
            'pallet'
        )
        weight_result = self.sale_order_shipping_cost.calculate_shipping_cost(
            1,
            10,
            'total_weight'
        )
        pallet_prices_obtained = [elem['price'] for elem in pallet_result]
        weight_prices_obtained = [elem['price'] for elem in weight_result]
        self.assertEqual(pallet_prices_expected, pallet_prices_obtained)
        self.assertEqual(weight_prices_expected, weight_prices_obtained)

    def test_get_service_price_list_correctly(self):
        translator_value = self.sale_order_shipping_cost.shipping_cost_id.weight_volume_translation
        expected_service_price_list = [{
            'price': 12.1,
            'sale_order_shipping_cost_id': self.sale_order_shipping_cost.id,
            'service_name': 'Good service test',
            'weight_volume_translation': translator_value
        }]

        base_price = 10
        obtained_service_price_list = self.sale_order_shipping_cost.get_service_price_list(
            base_price
        )

        self.assertEquals(expected_service_price_list, obtained_service_price_list)

    def test_fee_price_with_pallet_mode(self):
        expected_fee = 10
        pallet_number = 1
        shipping_weight = 10
        mode_of_fee = 'pallet'
        returned_fee = self.sale_order_shipping_cost.get_fee_price(
            pallet_number,
            shipping_weight,
            mode_of_fee
        )
        self.assertEqual(expected_fee, returned_fee)

    def test_fee_price_with_weight_mode(self):
        expected_fee = 15
        pallet_number = 1
        shipping_weight = 10
        mode_of_fee = 'total_weight'
        returned_fee = self.sale_order_shipping_cost.get_fee_price(
            pallet_number,
            shipping_weight,
            mode_of_fee
        )
        self.assertEqual(expected_fee, returned_fee)


class TestShippingCostCalculator(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_format = cls.env['postal.code.format'].create({
            'name': 'Test format',
            'regex': r'\AGood code$',
            'postal_code_sample': 'Good code'
        })
        cls.country = cls.env['res.country'].create({
            'name': 'Test Country',
            'postal_code_format_id': cls.postal_code_format.id
        })
        cls.shipping_cost_calculator = cls.env['shipping.cost.calculator'].create({
            'shipping_weight': 10,
            'shipping_volume': 1.0,
            'zip_code': 'Good code',
            'country_id': cls.country.id
        })
        cls.partner = cls.env['res.partner'].create({
            'company_type': 'person',
            'name': 'Test partner',
            'country_id': cls.country.id
        })
        cls.good_service = cls.env['transportation.service'].create({'name': 'Good service test'})
        cls.good_transporter = cls.env['transportation.transporter'].create({
            'name': 'Good transporter',
            'partner_id': cls.partner.id,
            'service_ids': [(4, cls.good_service.id)]
        })
        cls.good_zone = cls.env['shipping.zone'].create({
            'name': 'Good zone',
            'transporter_id': cls.good_transporter.id,
            'country_id': cls.country.id,
            'postal_code_ids': [
                (0, 0, {'first_code': 'Good code', 'last_code': 'Good code'})
            ]
        })

        cls.supplement_good_service = cls.env['shipping.cost.supplement'].create({
            'service_id': cls.good_service.id,
            'added_percentage': 10.0
        })
        cls.one_pallet_fee = cls.env['shipping.cost.fee'].create({
            'type': 'pallet',
            'max_qty': 1,
            'price': 10.0
        })
        cls.five_pallet_fee = cls.env['shipping.cost.fee'].create({
            'type': 'pallet',
            'max_qty': 5,
            'price': 30.0
        })
        cls.weight_50_fee = cls.env['shipping.cost.fee'].create({
            'type': 'total_weight',
            'max_qty': 50.0,
            'price': 15.0
        })
        cls.weight_100_fee = cls.env['shipping.cost.fee'].create({
            'type': 'total_weight',
            'max_qty': 100.0,
            'price': 20.0
        })
        cls.shipping_cost = cls.env['shipping.cost'].create({
            'cost_name': 'Test shipping cost',
            'fee_ids': [
                (4, cls.one_pallet_fee.id),
                (4, cls.five_pallet_fee.id),
                (4, cls.weight_50_fee.id),
                (4, cls.weight_100_fee.id)
            ],
            'volume': 5.0,
            'is_active': True,
            'transporter_id': cls.good_transporter.id,
            'supplement_ids': [(4, cls.supplement_good_service.id)],
            'shipping_zone_id': cls.good_zone.id
        })

    def test_calculate_shipping_cost(self):
        returned_action = self.shipping_cost_calculator.calculate_shipping_cost()
        picking_rated_returned = self.env['picking.rated.wizard'].browse(returned_action['res_id'])

        expected_currency_list = ['EUR', 'EUR']
        expected_prices = [11.0, 16.5]
        expected_service_names = ['Good service test'] * 2
        expected_transit_time = ['', '']

        obtained_currency_list = picking_rated_returned.data.mapped('currency')
        obtained_prices = picking_rated_returned.data.mapped('amount')
        obtained_service_names = picking_rated_returned.data.mapped('service')
        obtained_transit_time = [''] * 2

        self.assertEqual(expected_currency_list, obtained_currency_list)
        self.assertEqual(expected_prices, obtained_prices)
        self.assertEqual(expected_service_names, obtained_service_names)
        self.assertEqual(expected_transit_time, obtained_transit_time)

    def test_calculate_shipping_cost_with_negative_volume(self):
        self.shipping_cost_calculator.write({'shipping_volume': -1})
        with self.assertRaisesRegex(
            UserError,
            'Invalid values to calculate shipping costs. Please, try changing values.'
        ):
            self.shipping_cost_calculator.with_context({'lang': 'en'}).calculate_shipping_cost()

    def test_calculate_shipping_cost_with_negative_weight(self):
        self.shipping_cost_calculator.write({'shipping_weight': -1})
        with self.assertRaisesRegex(
            UserError,
            'Invalid values to calculate shipping costs. Please, try changing values.'
        ):
            self.shipping_cost_calculator.with_context({'lang': 'en'}).calculate_shipping_cost()

    def test_calculate_shipping_cost_with_zip_code_not_found(self):
        self.shipping_cost_calculator.write({'zip_code': 'Bad code'})
        with self.assertRaisesRegex(
            UserError,
            'There are no zones embedding "Bad code". Please, try with another zip code.'
        ):
            self.shipping_cost_calculator.with_context({'lang': 'en'}).calculate_shipping_cost()
