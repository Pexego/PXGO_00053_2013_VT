from odoo.tests.common import SavepointCase


class TestShippingCost(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # crear shipping_cost

        # crear_tarifas

        # crear_servicios

    def test_shipping_cost_created_with_services_that_are_not_from_the_transporter_raises_exception(self):
        pass

    def test_shipping_cost_created_with_shipping_zone_that_is_not_from_the_transporter_raises_exception(self):
        pass


class TestSaleOrderShippingCost(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # crear so

        # crear shipping_cost

        # crear_tarifas

        # crear_servicios

        # crear sale_order_shiping_cost

    def test_calculates_chipping_costs_correctly(self):
        pass
