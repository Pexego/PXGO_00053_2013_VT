from odoo.tests.common import SavepointCase


class TestSaleOrder(SavepointCase):
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
            'country_id': cls.country.id,
            'zip': '00052'
        })
        cls.good_service = cls.env['transportation.service'].create({'name': 'Good service test'})
        cls.good_transporter = cls.env['transportation.transporter'].create({
            'name': 'Good transporter',
            'partner_id': cls.partner.id,
            'fuel': 10.0,
            'service_ids': [(4, cls.good_service.id)]
        })

        cls.special_costs_product = cls.env['product.product'].create({
            'name': "Test special cost product",
            'default_code': "Test special cost product",
            'special_shipping_costs': True,
            'weight': 10,
            'volume': 1
        })
        cls.no_special_costs_product = cls.env['product.product'].create({
            'name': "Test not special cost product",
            'default_code': "Test not special cost product",
            'special_shipping_costs': False,
            'weight': 10,
            'volume': 1
        })
        cls.no_weight_volume_product = cls.env['product.product'].create({
            'name': "Test no weight or volume product",
            'default_code': "Test no weight or volume product",
            'special_shipping_costs': False
        })
        cls.uom_id = cls.env['product.uom'].search([('name', '=', 'Unit(s)')])[0]
        cls.pricelist = cls.env['product.pricelist'].search([('name', '=', 'Public Pricelist')])[0]
        cls.special_shipping_cost_sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'partner_shipping_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'delivery_type': 'shipping',
            'order_line': [
                (0, 0, {
                    'name': cls.special_costs_product.name,
                    'product_id': cls.special_costs_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                })]
        })
        cls.special_shipping_cost_sale_order.write({
            'transporter_id': cls.good_transporter.id
        })
        cls.no_special_shipping_cost_sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'partner_shipping_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'transporter_id': cls.good_transporter.id,
            'delivery_type': 'shipping',
            'order_line': [
                (0, 0, {
                    'name': cls.no_special_costs_product.name,
                    'product_id': cls.no_special_costs_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': cls.uom_id.id,
                    'price_unit': 100.0
                })]
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
            'transporter_id': cls.good_transporter.id,
            'country_id': cls.country.id,
            'postal_code_ids': [
                (0, 0, {'first_code': '56000', 'last_code': '56999'})
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
            'is_active': True,
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

    def test_get_sale_order_zone(self):
        zone_returned = self.special_shipping_cost_sale_order.get_sale_order_zone()
        self.assertTrue(zone_returned == self.good_zone)

    def test_compute_variables_without_special_shipping_costs(self):
        # we do not need to mock anything, because there is no shipment_group with test country
        res = self.no_special_shipping_cost_sale_order.compute_variables()
        picking_rated = self.env['picking.rated.wizard'].browse(res['res_id'])

        expected_currency_list = ['EUR', 'EUR']
        expected_amount_list = [12.1, 18.15]
        expected_service_list = ['Good service test', 'Good service test']
        expected_transit_time = ['', '']

        obtained_currency_list = picking_rated.data.mapped('currency')
        obtained_amount_list = picking_rated.data.mapped('amount')
        obtained_service_list = picking_rated.data.mapped('service')
        obtained_transit_time = picking_rated.data.mapped('transit_time')

        self.assertEqual(picking_rated.total_weight, '10.0')
        self.assertEqual(picking_rated.total_volume, '1.0')
        self.assertEqual(picking_rated.message_products_weight, '')
        self.assertEqual(picking_rated.message_products_volume, '')
        self.assertEqual(obtained_currency_list, expected_currency_list)
        self.assertEqual(obtained_amount_list, expected_amount_list)
        self.assertEqual(obtained_service_list, expected_service_list)
        self.assertEqual(obtained_transit_time, expected_transit_time)

    def test_compute_variables_with_special_shipping_costs_and_no_message(self):
        res = self.special_shipping_cost_sale_order.compute_variables()
        picking_rated = self.env['picking.rated.wizard'].browse(res['res_id'])
        expected_currency_list = ['EUR', 'EUR']
        expected_amount_list = [12.1, 18.15]
        expected_service_list = ['Good service test', 'Good service test']
        expected_transit_time = ['', '']

        obtained_currency_list = picking_rated.data.mapped('currency')
        obtained_amount_list = picking_rated.data.mapped('amount')
        obtained_service_list = picking_rated.data.mapped('service')
        obtained_transit_time = picking_rated.data.mapped('transit_time')

        self.assertEqual(picking_rated.total_weight, '10.0')
        self.assertEqual(picking_rated.total_volume, '1.0')
        self.assertEqual(picking_rated.message_products_weight, '')
        self.assertEqual(picking_rated.message_products_volume, '')
        self.assertEqual(obtained_currency_list, expected_currency_list)
        self.assertEqual(obtained_amount_list, expected_amount_list)
        self.assertEqual(obtained_service_list, expected_service_list)
        self.assertEqual(obtained_transit_time, expected_transit_time)

    def test_compute_variables_with_no_volume_and_weight_product(self):
        self.special_shipping_cost_sale_order.write({
            'order_line': [
                (0, 0, {
                    'name': self.no_weight_volume_product.name,
                    'product_id': self.no_weight_volume_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': self.uom_id.id,
                    'price_unit': 10.0
                })]
        })
        # we need to set transporter because it has changed with the last write
        self.special_shipping_cost_sale_order.write({
            'transporter_id': self.good_transporter.id
        })
        res = self.special_shipping_cost_sale_order.compute_variables()
        picking_rated = self.env['picking.rated.wizard'].browse(res['res_id'])

        expected_currency_list = ['EUR', 'EUR']
        expected_amount_list = [12.1, 18.15]
        expected_service_list = ['Good service test', 'Good service test']
        expected_transit_time = ['', '']
        expected_weight_message = ("1 of the product(s) of the order don't have "
                                   "set the weights, please take the shipping cost"
                                   " as an approximation")
        expected_volume_message = ("1 of the product(s) of the order don't have "
                                   "set the volumes, please take the shipping cost"
                                   " as an approximation")

        obtained_currency_list = picking_rated.data.mapped('currency')
        obtained_amount_list = picking_rated.data.mapped('amount')
        obtained_service_list = picking_rated.data.mapped('service')
        obtained_transit_time = picking_rated.data.mapped('transit_time')

        self.assertEqual(picking_rated.total_weight, '10.0')
        self.assertEqual(picking_rated.total_volume, '1.0')
        self.assertEqual(picking_rated.message_products_weight, expected_weight_message)
        self.assertEqual(picking_rated.message_products_volume, expected_volume_message)
        self.assertEqual(obtained_currency_list, expected_currency_list)
        self.assertEqual(obtained_amount_list, expected_amount_list)
        self.assertEqual(obtained_service_list, expected_service_list)
        self.assertEqual(obtained_transit_time, expected_transit_time)
