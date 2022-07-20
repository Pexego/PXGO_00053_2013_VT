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
        res = True
        for picking in self:
            if picking.picking_type_id == self.env.ref('stock_dropshipping.picking_type_dropship'):
                self.cancel_es_picking()
                res = super(StockPicking, self.sudo()).action_cancel()
            else:
                res = super(StockPicking, self).action_cancel()
        return res

    def get_email_template(self):
        if self.picking_type_id == self.env.ref('stock_dropshipping.picking_type_dropship'):
            return self.env.ref('dropship_italia_it.picking_done_dropship_template').with_context(lang=self.sale_id.partner_id.lang)
        return super(StockPicking, self).get_email_template()

    def check_send_email_base(self, vals):
        res = super(StockPicking, self).check_send_email_base(vals)
        return res and not self.partner_id.commercial_partner_id.country_code

    def check_send_email_extended(self, vals):
        res = super(StockPicking, self).check_send_email_base(vals)
        return res or self.picking_type_id == self.env.ref('stock_dropshipping.picking_type_dropship')
