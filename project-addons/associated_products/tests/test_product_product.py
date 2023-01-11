from odoo.tests.common import SavepointCase


class TestProductProduct(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super(TestProductProduct, cls).setUpClass()
        cls.product1 = cls.env['product.product'].create({
            'name': "Test",
            'default_code': "Test"
        })
        cls.product2 = cls.env['product.product'].create({
            'name': "Test1",
            'default_code': "Test1"
        })
        # arrange
        cls.equivalent = cls.env['product.equivalent'].create(
            {'product_id': cls.product1.id, 'equivalent_id': cls.product2.id})
        cls.equivalent2 = cls.env['product.equivalent'].create(
            {'product_id': cls.product1.id, 'product_name': 'TEST-NAME'})

    def test_verifies_that_compute_equivalent_products_return_all_products_equivalent_objets(self):
        #act
        products = self.product1.equivalent_products
        # assert
        self.assertEquals(products,self.product2 + self.product1)


    def test_verifies_that_search_equivalent_products_return_all_products_equivalent_objets(self):
        #act
        products = self.env['product.product'].search([('equivalent_products','=',self.product1.default_code)])
        # assert
        self.assertEquals(products, self.product2 + self.product1)

    def test_verifies_that_search_equivalent_products_return_all_products_objets_searching_by_product_name_without_equivalent_product_object(self):
        #act
        products = self.env['product.product'].search([('equivalent_products','=',self.equivalent2.product_name)])
        # assert
        self.assertEquals(products, self.product1)

    def test_verifies_that_search_equivalent_products_return_no_products_objets_searching_by_no_existing_product_name(self):
        #act
        products = self.env['product.product'].search([('equivalent_products','=','TEST-NAME2')])
        # assert
        self.assertEquals(products, self.env['product.product'])

