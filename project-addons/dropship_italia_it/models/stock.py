from odoo import models, api, fields, exceptions, _
import odoorpc


class StockPicking(models.Model):

    _inherit = "stock.picking"

    picking_es_id = fields.Integer()
    picking_es_str = fields.Char("ES picking")

    @api.multi
    def cancel_es_picking(self):
        # get the server
        server = self.env['base.synchro.server'].search([('name', '=', 'Visiotech')])
        # Prepare the connection to the server
        odoo_es = odoorpc.ODOO(server.server_url, port=server.server_port)
        # Login
        odoo_es.login(server.server_db, server.login, server.password)

        for picking in self:
            picking_es = odoo_es.env['stock.picking'].browse(picking.picking_es_id)
            try:
                picking_es.action_cancel()
            except:
                raise exceptions.UserError(_('The order cannot be canceled'))

    @api.multi
    def action_cancel(self):
        for picking in self:
            if picking.picking_type_id == self.env.ref('stock_dropshipping.picking_type_dropship'):
                self.cancel_es_picking()
                res = super(StockPicking, self.sudo()).action_cancel()
            else:
                res = super(StockPicking, self).action_cancel()
        return res
