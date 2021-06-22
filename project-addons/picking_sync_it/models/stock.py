from odoo import models, fields, api, _
from odoo.addons.queue_job.job import job
import odoorpc


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def action_done(self):
        res = super().action_done()
        for picking in self:
            if picking.picking_type_id.id == self.env.ref('automatize_edi_it.picking_type_receive_top_deposit').id:
                # Notify odoo ES that the picking is done
                self.with_delay(eta=10, priority=8).notify_picking_done(picking.purchase_id.remark)
        return res

    @api.multi
    def retry_notify_picking_done(self):
        for pick in self:
            pick.notify_picking_done(pick.purchase_id.remark)

    @job(retry_pattern={1: 10 * 60})
    def notify_picking_done(self, order):
        # get the server
        server = self.env['base.synchro.server'].search([('name', '=', 'Visiotech')])
        # Prepare the connection to the server
        odoo_es = odoorpc.ODOO(server.server_url, port=server.server_port)
        # Login
        odoo_es.login(server.server_db, server.login, server.password)

        order_es_id = odoo_es.env['sale.order'].search([('name', '=', order)])
        order_es = odoo_es.env['sale.order'].browse(order_es_id)

        for picking in order_es.picking_ids:
            if picking.not_sync and picking.location_id.name == 'Tránsito Italia' and picking.state == 'assigned':
                # Check if the qty done match with the origin, if not, make the partial
                if picking.qty == self.qty:
                    picking.action_done()
                else:
                    # Prior to make the partial, we put the qty done on each move
                    for move in self.move_lines:
                        for move_es in picking.move_lines:
                            if move.product_id.default_code == move_es.product_id.default_code:
                                move_es.qty_ready = move.quantity_done
                                move_es.quantity_done = move.quantity_done
                                break
                    picking.with_incidences = True
                    picking.move_type = 'direct'
                    picking.action_accept_ready_qty()
