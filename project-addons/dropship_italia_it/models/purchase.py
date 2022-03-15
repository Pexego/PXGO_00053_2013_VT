from odoo import models, api
import odoorpc


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    def prepare_order_es(self, purchase, odoo_es):
        if purchase.dest_address_id.dropship or not purchase.dest_address_id.parent_id:
            name_ship = purchase.dest_address_id.name
        else:
            name_ship = purchase.dest_address_id.commercial_partner_id.name + ', ' + purchase.dest_address_id.name
        partner = odoo_es.env['res.partner'].search([('name', '=', 'VISIOTECH Italia'), ('is_company', '=', True)])
        partner_ship = odoo_es.env['res.partner'].search([('name', '=', name_ship),
                                                          ('zip', '=', purchase.dest_address_id.zip),
                                                          ('street', '=', purchase.dest_address_id.street),
                                                          ('city', '=', purchase.dest_address_id.city),
                                                          ('dropship', '=', True),
                                                          ('parent_id', '=', partner[0]),
                                                          ('type', '=', 'delivery'),
                                                          ('active', '=', False)])
        if not partner_ship:
            state = odoo_es.env['res.country.state'].search([('name', '=', purchase.dest_address_id.state_id.name)])
            country = odoo_es.env['res.country'].search([('code', '=', purchase.dest_address_id.country_id.code)])
            partner_vals = {
                'name': name_ship,
                'dropship': True,
                'email': purchase.dest_address_id.email,
                'customer': True,
                'is_company': False,
                'delivery_type': 'shipping',
                'parent_id': partner[0],
                'type': 'delivery',
                'street': purchase.dest_address_id.street,
                'city': purchase.dest_address_id.city,
                'zip': purchase.dest_address_id.zip,
                'country_id': country[0],
                'state_id': state[0],
            }
            partner_ship_id = odoo_es.env['res.partner'].create(partner_vals)
            partner_ship = [partner_ship_id]
        vals = {
            'partner_id': partner[0],
            'partner_shipping_id': partner_ship[0],
            'state': 'reserve',
            'no_promos': True,
            'allow_confirm_blocked_magreb': True,
            'client_order_ref': purchase.name
        }
        return vals

    def prepare_order_line_es(self, line, order_es, odoo_es):
        product = odoo_es.env['product.product'].search([('default_code', '=', line.product_id.default_code)])
        vals = {
            'order_id': order_es,
            'product_id': product[0],
            'product_uom_qty': line.product_qty,
            'price_unit': line.price_unit,
            'discount': line.discount
        }
        return vals

    @api.multi
    def confirm_and_create_order_es(self):
        self.ensure_one()
        # get the server
        server = self.env['base.synchro.server'].search([('name', '=', 'Visiotech')])
        # Prepare the connection to the server
        odoo_es = odoorpc.ODOO(server.server_url, port=server.server_port)
        # Login
        odoo_es.login(server.server_db, server.login, server.password)

        # Confirm purchase order
        context = self._context.copy()
        context['bypass_override'] = True
        context.pop('default_state', False)
        self.with_context(context).sudo().button_confirm()
        for pick in self.picking_ids:
            pick.not_sync = True

        # Create the sale order in ES
        vals = self.prepare_order_es(self, odoo_es)
        order_es_id = odoo_es.env['sale.order'].create(vals)
        order_es = odoo_es.env['sale.order'].browse(order_es_id)
        order_es.onchange_partner_id()
        order_es.write({'partner_shipping_id': vals['partner_shipping_id']})

        for line in self.order_line:
            l_vals = self.prepare_order_line_es(line, order_es_id, odoo_es)
            odoo_es.env['sale.order.line'].create(l_vals)

        product_ship = odoo_es.env['product.product'].search([('default_code', '=', 'SPEDIZIONE')])
        vals_ship = {
            'order_id': order_es_id,
            'product_id': product_ship[0],
            'product_uom_qty': 1,
            'discount': 100
        }
        odoo_es.env['sale.order.line'].create(vals_ship)

        order_es.action_confirm()

        picking_es_ids = odoo_es.env['stock.picking'].search([('origin', '=', order_es.name)])
        picking_es = odoo_es.env['stock.picking'].browse(picking_es_ids)

        for pick in self.picking_ids:
            pick.picking_es_id = picking_es_ids[0]
            pick.picking_es_str = picking_es.name
