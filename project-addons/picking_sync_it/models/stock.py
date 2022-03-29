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
    def action_cancel(self):
        for picking in self:
            if picking.picking_type_id.id == self.env.ref('automatize_edi_it.picking_type_receive_top_deposit').id:
                # Launch job to cancel the draft moves of the PO
                picking.purchase_id.with_delay(eta=1800, priority=8).cancel_draft_moves()
                # Notify odoo ES that the picking is canceled
                # Wait two hours to ensure the action_done have finished
                self.with_delay(eta=7200, priority=8).notify_picking_cancel(picking.purchase_id.remark, picking.get_signature())
        res = super().action_cancel()
        return res

    @api.multi
    def retry_notify_picking_done(self):
        for pick in self:
            pick.notify_picking_done(pick.purchase_id.remark)

    @job()
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
            elif picking.location_id.name == 'Tránsito Italia' and picking.state != 'assigned':
                mail_pool = self.env['mail.mail']
                context = self._context.copy()
                context.pop('default_state', False)
                context['message_warn'] = 'Entrada %s recibida. Imposible notificar finalización. Revisar el pedido %s' \
                                          % (self.name, order)

                template_id = self.env.ref('picking_sync_it.email_template_sync_pick_error')

                if template_id:
                    mail_id = template_id.with_context(context).send_mail(self.id)
                    if mail_id:
                        mail_id_check = mail_pool.browse(mail_id)
                        mail_id_check.with_context(context).send()

    @job(retry_pattern={1: 10 * 60})
    def notify_picking_cancel(self, order, signature):
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
                # Check if the signature match with the origin
                if picking.get_signature() == signature:
                    picking.action_cancel()
                else:
                    mail_pool = self.env['mail.mail']
                    context = self._context.copy()
                    context.pop('default_state', False)
                    context['message_warn'] = 'Entrada %s cancelada. No se ha encontrado una entrada similar en España. Revisar el pedido %s' \
                                              % (self.name, order)

                    template_id = self.env.ref('picking_sync_it.email_template_sync_pick_error')

                    if template_id:
                        mail_id = template_id.with_context(context).send_mail(self.id)
                        if mail_id:
                            mail_id_check = mail_pool.browse(mail_id)
                            mail_id_check.with_context(context).send()
