
from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    post_install = True
    at_install = True

    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.so_model = self.env['sale.order']
        self.res_partner_model = self.env['res.partner']

    def test_change_is_project_from_false_to_true(self):
        #arrange
        partner_id = self.res_partner_model.create(dict(name="Peter"))
        so_vals = {'partner_id': partner_id.id,
                   'not_sync_picking':False,
                   'no_promos':False
                   }
        order = self.so_model.create(so_vals)

        #act
        order.is_project = True
        order.onchange_is_project()

        #assert
        self.assertEqual(order.not_sync_picking, True)
        self.assertEqual(order.no_promos, True)

    def test_change_is_project_from_true_to_false(self):
        #arrange
        partner_id = self.res_partner_model.create(dict(name="Peter"))
        so_vals = {'partner_id': partner_id.id,
                   'not_sync_picking':False,
                   'no_promos':False,
                   'is_project':True
                   }
        order = self.so_model.create(so_vals)

        #act
        order.is_project = False
        order.onchange_is_project()

        #assert
        self.assertEqual(order.not_sync_picking, False)
        self.assertEqual(order.no_promos, False)
