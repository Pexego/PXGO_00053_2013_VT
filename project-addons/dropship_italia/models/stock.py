from odoo import models, fields, api, _, exceptions
from odoo.addons.queue_job.job import job
import odoorpc


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def action_done(self):
        res = super().action_done()
        for picking in self:
            if picking.sale_id.partner_id.name == 'VISIOTECH Italia' and picking.partner_id.dropship:
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

        #TODO: hacer comprobaciones de si está parcializado el de ES

        for picking in purchase_it.picking_ids:
            if picking.not_sync and picking.state == 'assigned' \
                    and picking.picking_type_id == odoo_it.env.ref('stock_dropshipping.picking_type_dropship'):
                # Check if the qty done match with the origin
                if picking.qty == self.qty:
                    picking.action_done()
                    picking.write({'carrier_tracking_ref': self.carrier_tracking_ref,
                                   'carrier_name': self.carrier_name})

    @api.multi
    def action_cancel(self):
        for picking in self:
            if picking.sale_id.partner_id.name == 'VISIOTECH Italia' \
                    and picking.sale_id.partner_shipping_id.dropship and not self.env.user.has_group('base.group_system'):
                raise exceptions.UserError(_('This order cannot be canceled here, should be canceled in Italy'))
        return super(StockPicking, self).action_cancel()