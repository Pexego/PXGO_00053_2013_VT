from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests


class StockPickingVstock(models.Model):
    _name = 'stock.picking.vstock'

    '''Este modelo se ha creado para evitar escribir el albarán con los
    datos de vstock y que vstock vuelva a leerlo, ocasionando problemas.'''

    state_papeur = fields.Selection([('notified', 'Notified'), ('urgent', 'Urgent'), ('done', 'Done')],
                                    string="Notified")
    id_vstock = fields.Char()
    state_vstock = fields.Char()
    user_vstock = fields.Char()
    last_date_vstock = fields.Datetime(default=fields.Datetime.now)
    date_done_vstock = fields.Datetime()
    picking_id = fields.Many2one('stock.picking')

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for picking_data in self:
            web_endpoint = None
            if vals.get('date_done_vstock', False) and picking_data.state_papeur in ('notified', 'urgent'):
                ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
                web_endpoint = f'{ppu_endpoint}/ready'
                picking_data.picking_id.cancel_order_urgent()
                picking_data.state_papeur = 'done'
                picking_data.picking_id.with_delay(priority=1, eta=1800).auto_deliver_order()
            elif vals.get('id_vstock') and not picking_data.state_papeur:
                ppu_auto_notify = eval(self.env['ir.config_parameter'].sudo().get_param('papeur.auto.notify.array'))
                if picking_data.picking_id.partner_id in ppu_auto_notify:
                    picking_data.picking_id.prepare_order()
            elif 'state_vstock' in vals and picking_data.state_papeur in ('notified', 'urgent'):
                if vals.get('state_vstock') == 'En preparación':
                    ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
                    web_endpoint = f'{ppu_endpoint}/doing'

            if web_endpoint:
                data = {
                    "name": f"{picking_data.picking_id.origin or ''} - {picking_data.picking_id.name}",
                    "odoo_id": picking_data.picking_id.id
                }
                try:
                    response = requests.post(web_endpoint, json=data)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    raise UserError(_("Something went wrong: %s" % e))

            if vals.get('user_vstock') and picking_data.state_papeur in ('notified', 'urgent'):
                picking_data.picking_id.notify_user()

        return res

    @api.multi
    def create_rpc(self, vals):
        return self.create(vals)

