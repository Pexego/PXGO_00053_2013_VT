from odoo.tests.common import SavepointCase


class TestProductProduct(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_1 = cls.env['product.product'].create({
            'name': 'product_1',
            'default_code': 'product_1',
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'product_2',
            'default_code': 'product_2',
            'replacement_id': cls.product_1.id,
            'final_replacement_id': cls.product_1.id
        })
        cls.product_3 = cls.env['product.product'].create({
            'name': 'product_3',
            'default_code': 'product_3',
            'replacement_id': cls.product_2.id,
            'final_replacement_id': cls.product_1.id
        })
        cls.product_4 = cls.env['product.product'].create({
            'name': 'product_4',
            'default_code': 'product_4',
            'replacement_id': cls.product_2.id,
            'final_replacement_id': cls.product_1.id
        })
        cls.product_5 = cls.env['product.product'].create({
            'name': 'product_5',
            'default_code': 'product_5'
        })

    def test_search_cycles_with_cycle(self):
        self.product_1.replacement_id = self.product_4
        obtained_result = self.product_4.search_cycle(self.product_4)
        self.assertTrue(obtained_result)

    def test_search_cycles_with_no_cycles(self):
        obtained_result = self.product_4.search_cycle(self.product_4)
        self.assertFalse(obtained_result)
