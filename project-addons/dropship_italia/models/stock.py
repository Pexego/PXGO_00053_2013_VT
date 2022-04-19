from odoo import models, fields, api, _, exceptions
from odoo.addons.queue_job.job import job
import odoorpc


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def action_done(self):
        res = super().action_done()
        for picking in self:
            if picking.sale_id.partner_id.commercial_partner_id.country_code and picking.partner_id.dropship:
                # Notify odoo IT the dropship is done
                self.with_delay(eta=10, priority=8).notify_dropship_done()
        return res

    @job(retry_pattern={1: 10 * 60})
    @api.multi
    def notify_dropship_done(self):
        # get the server
        server = self.env['base.synchro.server'].sudo().search([('name', '=', 'Visiotech IT')])
        # Prepare the connection to the server
        odoo_it = odoorpc.ODOO(server.server_url, port=server.server_port)
        # Login
        odoo_it.login(server.server_db, server.login, server.password)

        purchase_it_id = odoo_it.env['purchase.order'].search([('name', '=', self.sale_id.client_order_ref)])
        purchase_it = odoo_it.env['purchase.order'].browse(purchase_it_id)
        picking_it_ids = purchase_it.picking_ids.mapped('id')

        for picking in purchase_it.picking_ids:
            if picking.not_sync and picking.state == 'assigned' \
                    and picking.picking_type_id.id == odoo_it.env.ref('stock_dropshipping.picking_type_dropship').id:
                # Check if the qty done match with the origin
                if picking.qty == self.qty:
                    picking.action_done()
                    picking.write({'carrier_tracking_ref': self.carrier_tracking_ref,
                                   'carrier_name': self.carrier_name})
                    picking.create_invoice()
                elif picking.qty > self.qty:
                    done_lines = {li.product_id.name: li.quantity_done for li in self.move_lines}
                    # Divide IT pick
                    for line in picking.move_lines:
                        if line.product_id.name in done_lines.keys():
                            line.write({'qty_ready': done_lines[line.product_id.name],
                                        'quantity_done': done_lines[line.product_id.name]})
                            done_lines.pop(line.product_id.name)

                    picking.with_incidences = True
                    picking.move_type = 'direct'
                    picking.action_accept_ready_qty()
                    picking.write({'carrier_tracking_ref': self.carrier_tracking_ref,
                                   'carrier_name': self.carrier_name})
                    picking.create_invoice()
                    # Browse again the purchase to get the brand new picking just created
                    new_purchase_it = odoo_it.env['purchase.order'].browse(purchase_it_id)
                    new_picking = self.env['stock.picking'].search([('backorder_id', '=', self.id)])
                    for new_picking_it in new_purchase_it.picking_ids:
                        if new_picking_it.id not in picking_it_ids:
                            new_picking_it.picking_es_id = new_picking.id
                            new_picking_it.picking_es_str = new_picking.name
                            break

    @api.multi
    def action_cancel(self):
        for picking in self:
            if picking.sale_id.partner_id.commercial_partner_id.country_code \
                    and picking.sale_id.partner_shipping_id.dropship and not self.env.user.has_group('base.group_system'):
                raise exceptions.UserError(_('This order cannot be canceled here, should be canceled in Italy'))
        return super(StockPicking, self).action_cancel()
