from odoo.tests.common import SavepointCase
import datetime


class TestStockLandedCost(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': "Test Product",
            'default_code': "Test Product",
            'state': 'sellable'
        })

        cls.account_journal = cls.env['account.journal'].create({
            'name': 'Test Account Journal',
            'type': 'sale',
            'code': '12345'
        })

        cls.stock_landed_cost = cls.env['stock.landed.cost'].create({
            'date': datetime.date.today(),
            'account_journal_id': cls.account_journal.id,
            'forwarder_invoice': 'Test FWDR',
        })
        cls.stock_line_by_tariff = cls.env['stock.landed.cost.lines'].create({
            'cost_id': cls.stock_landed_cost.id,
            'product_id': cls.product.id,
            'split_method': 'by_tariff',
            'price_unit': 12
        })
        cls.stock_line_to_define = cls.env['stock.landed.cost.lines'].create({
            'cost_id': cls.stock_landed_cost.id,
            'product_id': cls.product.id,
            'split_method': 'to_define',
            'price_unit': 10
        })

    def test_check_if_all_lines_have_split_method_with_split_method_lines(self):
        expected_value = False
        obtained_value = self.stock_landed_cost.check_if_all_lines_have_split_method(
            self.stock_landed_cost.cost_lines
        )
        self.assertEqual(expected_value, obtained_value)

    def test_check_if_all_lines_have_split_method_with_no_split_method_lines(self):
        expected_value = True
        self.stock_landed_cost.write({
            'cost_lines': [(3, self.stock_line_to_define.id)]
        })
        obtained_value = self.stock_landed_cost.check_if_all_lines_have_split_method(
            self.stock_landed_cost.cost_lines
        )
        self.assertEqual(expected_value, obtained_value)
