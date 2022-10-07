from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    post_install = True
    at_install = True

    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.so_model = self.env['sale.order']
        self.res_partner_model = self.env['res.partner']
        self.deposits_model = self.env['stock.deposit']
        self.move_id = self.env['stock.move']
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.uom_unit = self.env.ref('product.product_uom_unit')

    def test_action_view_deposits_when_there_are_deposits(self):
        # arrange
        partner_id = self.res_partner_model.create(dict(name="Peter"))
        so_vals = {'partner_id': partner_id.id
                   }
        order = self.so_model.create(so_vals)
        product = self.env['product.product'].create({
            'name': 'Product A',
            'default_code': 'Product A',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        move = self.env['stock.move'].create({
            'name': 'test_in_1',
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'product_id': product.id,
            'product_uom': self.uom_unit.id,
            'product_uom_qty': 100.0,
        })
        deposit = self.deposits_model.create(
            {'sale_id': order.id, 'move_id': move.id, 'product_id': product.id, 'state': 'draft'})
        order.deposit_ids = [(4, deposit.id)]
        deposits_domain = [('id', 'in', deposit.ids)]

        # act
        action = order.action_view_deposits()

        # assert
        self.assertEqual(action.get('domain', []), deposits_domain)
        self.assertEqual(action.get('type', False), 'ir.actions.act_window')

    def test_action_view_deposits_when_there_are_no_deposits(self):
        # arrange
        partner_id = self.res_partner_model.create(dict(name="Peter"))
        so_vals = {'partner_id': partner_id.id
                   }
        order = self.so_model.create(so_vals)

        # act
        action = order.action_view_deposits()

        # assert
        self.assertFalse(action.get('domain', False))
        self.assertFalse(action.get('context', False))
        self.assertEqual(action.get('type', False), 'ir.actions.act_window_close')
