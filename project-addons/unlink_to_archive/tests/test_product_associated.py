
from odoo.tests.common import TransactionCase


class TestProductAssociated(TransactionCase):
    post_install = True
    at_install = True

    def setUp(self):
        super(TestProductAssociated, self).setUp()
        self.product_model = self.env['product.product']


    def test_when_unlink_a_product_associated_must_be_archived(self):
        #arrange
        product_id = self.product_model.create({'name': "Test",
                                                    'default_code': "Test"})
        uom_unit = self.env.ref('product.product_uom_unit')

        product_id2 = self.product_model.create({'name': "Test2",
                                                      'default_code': "Test2",
                                                 'associated_product_ids':[(0,0,{'associated_id':product_id.id,
                                                                                 'quantity':1,
                                                                                 'uom_id':uom_unit.id})]
                                                    })

        #act
        associated_product = product_id2.associated_product_ids
        associated_product.unlink()

        #assert
        self.assertFalse(associated_product.active)
        self.assertTrue(associated_product.exists())

