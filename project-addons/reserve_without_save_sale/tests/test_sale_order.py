from odoo.tests.common import TransactionCase
from mock import patch

class TestSaleOrder(TransactionCase):
    post_install = True
    at_install = True

    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.so_model = self.env['sale.order']
        self.so_line_model = self.env['sale.order.line']
        self.res_partner_model = self.env['res.partner']

    def test_order_reserve_when_order_is_in_an_allowed_state(self):
        # Allowed states are Draft, Reserve and Sent
        # arrange
        partner_id = self.res_partner_model.create(dict(name="Peter"))
        order_draft = self.so_model.create({'partner_id': partner_id.id,
                                             'state': 'draft'
                                             })
        order_reserve= self.so_model.create({'partner_id': partner_id.id,
                                           'state': 'reserve'
                                           })
        order_sent = self.so_model.create({'partner_id': partner_id.id,
                                           'state': 'sent'
                                           })
        # act
        with patch('odoo.addons.reserve_without_save_sale.models.sale.SaleOrderLine.stock_reserve') as stock_reserve_mock:
            r1 = order_draft.order_reserve()
            r2 = order_reserve.order_reserve()
            r3 = order_sent.order_reserve()
        # assert
        self.assertTrue(r1)
        self.assertEqual(order_draft.state, 'reserve')
        self.assertTrue(r2)
        self.assertEqual(order_reserve.state, 'reserve')
        self.assertTrue(r3)
        self.assertEqual(order_sent.state, 'reserve')
        self.assertEqual(stock_reserve_mock.call_count, 3)

    def test_order_reserve_when_order_is_in_an_forbidden_state(self):
        # Forbidden states are Sale, Done and Cancel
        # arrange
        partner_id = self.res_partner_model.create(dict(name="Peter"))
        order_cancel = self.so_model.create({'partner_id': partner_id.id,
                                             'state': 'cancel'
                                             })
        order_done = self.so_model.create({'partner_id': partner_id.id,
                                           'state': 'done'
                                           })
        order_sale = self.so_model.create({'partner_id': partner_id.id,
                                           'state': 'sale'
                                           })

        # act
        r1 = order_cancel.order_reserve()
        r2 = order_done.order_reserve()
        r3 = order_sale.order_reserve()

        # assert
        self.assertFalse(r1)
        self.assertEqual(order_cancel.state, 'cancel')
        self.assertFalse(r2)
        self.assertEqual(order_done.state, 'done')
        self.assertFalse(r3)
        self.assertEqual(order_sale.state, 'sale')
