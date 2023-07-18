from odoo import models, api, _, fields
from odoo.exceptions import UserError
import requests
from odoo.addons.queue_job.job import job


class StockPicking(models.Model):

    _inherit = "stock.picking"

    state_papeur = fields.Selection([('notified', 'Notified'), ('urgent', 'Urgent')],
                                    string="Notified")
    id_vstock = fields.Char()
    state_vstock = fields.Char()
    user_vstock = fields.Char()
    last_date_vstock = fields.Datetime(default=lambda self: fields.Datetime.now())
    date_done_vstock = fields.Datetime()

    @api.multi
    def prepare_order(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/prepare_order'
        for picking in self:
            data = {
                "name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                "odoo_id": picking.id,
            }
            try:
                response = requests.post(web_endpoint, json=data)
            except:
                raise UserError(_("Something went wrong"))
            picking.state_papeur = 'notified'

    @api.multi
    def prepare_order_urgent(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/urgent_order'
        for picking in self:
            data = {
                "name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
            except:
                raise UserError(_("Something went wrong"))
            picking.state_papeur = 'urgent'

    @api.multi
    def cancel_order_urgent(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/cancel_order'
        web_endpoint_reception = f'{ppu_endpoint}/cancel_order_reception'
        for picking in self:
            data = {
                "name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                "odoo_id": picking.id
            }
            data_reception = {
                "name": f"{picking.origin or ''} - {picking.name}",
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
                response = requests.post(web_endpoint_reception, json=data_reception)
            except:
                raise UserError(_("Something went wrong"))
            picking.state_papeur = False

    @api.multi
    def deliver_order(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/deliver_order'
        for picking in self:
            data = {
                "name": f"{picking.origin or ''} - {picking.name}",
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
            except:
                raise UserError(_("Something went wrong"))

    @api.multi
    def notify_user(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/assign_user'
        for picking in self:
            data = {
                "name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                "user": picking.user_vstock,
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
            except:
                raise UserError(_("Something went wrong"))

    @api.model
    def return_orders(self):
        pickings = self.env['stock.picking'].search([('state', '=', 'assigned'),
                                                    ('picking_type_code', '=', 'outgoing'),
                                                    ('state_papeur', '!=', False)])

        orders = [{"name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                   "odoo_id": picking.id,
                   "state": picking.state_papeur,
                   "user": picking.user_vstock} for picking in pickings]
        return orders

    @api.model
    def return_orders_reception(self):
        pickings = self.env['stock.picking'].search([('state', '=', 'assigned'),
                                                     ('picking_type_code', '=', 'outgoing'),
                                                     ('state_papeur', '!=', False)])
        orders = [{"name": f"{picking.origin or ''} - {picking.name}",
                   "odoo_id": picking.id,
                   "state": picking.state_papeur,
                   "state_vstock": picking.state_vstock} for picking in pickings]
        return orders

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for picking in self:
            web_endpoint = None
            if vals.get('date_done_vstock', False):
                ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
                web_endpoint = f'{ppu_endpoint}/ready'
                picking.cancel_order_urgent()
                picking.with_delay(priority=1, eta=1800).auto_deliver_order()
            elif 'state_vstock' in vals:
                if vals.get('state_vstock') == 'En preparación':
                    ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
                    web_endpoint = f'{ppu_endpoint}/doing'
                elif vals.get('state_vstock') != 'En preparación' and picking.state_papeur:
                    ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
                    web_endpoint = f'{ppu_endpoint}/notified'
            elif vals.get('state_papeur', '') == 'notified':
                ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
                web_endpoint = f'{ppu_endpoint}/notified'

            if web_endpoint:
                data = {
                    "name": f"{picking.origin or ''} - {picking.name}",
                    "odoo_id": picking.id
                }
                try:
                    response = requests.post(web_endpoint, json=data)
                except:
                    raise UserError(_("Something went wrong"))

            if vals.get('user_vstock') and picking.state_papeur:
                picking.notify_user()

            if vals.get('id_vstock'):
                ppu_auto_notify = eval(self.env['ir.config_parameter'].sudo().get_param('papeur.auto.notify.array'))
                if picking.partner_id in ppu_auto_notify:
                    picking.prepare_order()

        return res

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60})
    @api.multi
    def auto_deliver_order(self):
        for pick in self:
            pick.deliver_order()
