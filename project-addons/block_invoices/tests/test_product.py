from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    post_install = True
    at_install = True

    def test_verifies_the_exclude_margin_field_is_marked_when_a_product_becomes_eol(self):
        # arrange
        product_id = self.env['product.product'].create({'name': "Test",
                                                   'default_code': "Test",
                                                   'state': 'sellable'
                                                   })
        # act
        product_id.product_tmpl_id.write({'state':'end'})

        # assert
        self.assertTrue(product_id.exclude_margin)

    def test_verifies_the_exclude_margin_field_is_not_marked_when_write_a_state_no_eol(self):
        # arrange
        product_id = self.env['product.product'].create({'name': "Test",
                                                   'default_code': "Test",
                                                   'state': 'draft'
                                                   })
        # act
        product_id.product_tmpl_id.write({'state':'sellable'})

        # assert
        self.assertFalse(product_id.exclude_margin)
