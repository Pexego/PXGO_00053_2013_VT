from odoo.tests.common import SavepointCase
import datetime
from unittest.mock import patch


class TestImportSheet(SavepointCase):
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

        cls.container = cls.env['stock.container'].create({
            'name': 'Test container',
            'type': 'air'
        })
        cls.import_sheet = cls.env['import.sheet'].create({
            'container_id': cls.container.id,
            'dua': 'Test Dua',
            'freight': 10,
            'inspection': 15,
            'fee': 20,
            'arrival_cost': 30
        })

        cls.stock_landed_cost = cls.env['stock.landed.cost'].create({
            'date': datetime.date.today(),
            'account_journal_id': cls.account_journal.id,
            'forwarder_invoice': 'Test FWDR',
            'import_sheet_id': cls.import_sheet.id
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

    def test_calculate_destination_cost_price(self):
        expected_cost = 55
        obtained_cost = self.import_sheet.calculate_destination_cost_price()

        self.assertEquals(expected_cost, obtained_cost)

    def test_calculate_fee_price(self):
        expected_cost = 20
        obtained_cost = self.import_sheet.calculate_fee_price()

        self.assertEquals(expected_cost, obtained_cost)

    def test_get_landed_cost_creator_wizard(self):
        expected_container = self.container
        expected_sheet = self.import_sheet
        expected_product_count = 0

        wzd = self.import_sheet.get_landed_cost_creator_wizard()

        obtained_container = wzd.container_id
        obtained_sheet = wzd.import_sheet_id
        obtained_product_count = len(wzd.product_ids)

        self.assertEquals(expected_container, obtained_container)
        self.assertEquals(expected_sheet, obtained_sheet)
        self.assertEquals(expected_product_count, obtained_product_count)

    def test_action_open_landed_cost_by_sheet(self):
        expected_domain = [('import_sheet_id', '=', self.import_sheet.id)]
        action_returned = self.import_sheet.action_open_landed_cost_by_sheet()
        obtained_domain = action_returned['domain']

        self.assertEquals(expected_domain, obtained_domain)

    def test_action_open_landed_cost_creator(self):
        wizard_to_create = self.env['landed.cost.creator.wizard'].create({
            'import_sheet_id': self.import_sheet.id
        })
        expected_res_id = wizard_to_create.id
        with patch(
            'odoo.addons.pmp_landed_costs.models.import_sheet.ImportSheet.get_landed_cost_creator_wizard'
        ) as get_landed_cost_creator_wizard_mock:
            get_landed_cost_creator_wizard_mock.return_value = wizard_to_create
            action_returned = self.import_sheet.action_open_landed_cost_creator()
        obtained_res_id = action_returned['res_id']

        self.assertEquals(expected_res_id, obtained_res_id)
