from odoo.tests.common import SavepointCase


class TestProductEquivalent(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super(TestProductEquivalent, cls).setUpClass()
        cls.product1 = cls.env['product.product'].create({
            'name': "Test",
            'default_code': "Test"
        })
        cls.product2 = cls.env['product.product'].create({
            'name': "Test1",
            'default_code': "Test1",
        })

    def test_verifies_that_create_inverse_relation_when_create_an_equivalent_product_and_it_doesnt_exist(self):
        #act
        self.env['product.equivalent'].create(
            {'product_id': self.product1.id, 'equivalent_id': self.product2.id})
        # assert
        product = self.env['product.equivalent'].search([('equivalent_id','=',self.product1.id),('product_id','=', self.product2.id)])
        self.assertEquals(len(product),1)


    def test_verifies_that_no_create_inverse_relation_when_create_an_equivalent_product_and_it_exists(self):
        # arrange
        self.env['product.equivalent'].create(
            {'product_id': self.product1.id, 'equivalent_id': self.product2.id})
        equivalent_products = self.product1.equivalent_products
        # act
        self.env['product.equivalent'].create(
            {'product_id': self.product2.id, 'equivalent_id': self.product1.id})
        # assert
        equivalent_products_2 = self.product1.equivalent_products
        self.assertEquals(len(equivalent_products), len(equivalent_products_2))

