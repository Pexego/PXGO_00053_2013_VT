from odoo import models, api, _, fields
from odoo.exceptions import UserError
import requests
from odoo.addons.queue_job.job import job


class StockPicking(models.Model):

    _inherit = "stock.picking"

    state_papeur = fields.Selection(related="vstock_data.state_papeur", readonly=True)
    id_vstock = fields.Char(related='vstock_data.id_vstock', readonly=True)
    state_vstock = fields.Char(related='vstock_data.state_vstock', readonly=True)
    user_vstock = fields.Char(related='vstock_data.user_vstock', readonly=True)
    last_date_vstock = fields.Datetime(related='vstock_data.last_date_vstock', readonly=True)
    date_done_vstock = fields.Datetime(related='vstock_data.date_done_vstock', readonly=True)

    vstock_data = fields.One2many('stock.picking.vstock', 'picking_id')

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for picking in self:
            if vals.get('block_picking', False) and vals.get('block_picking') is True and picking.state_papeur in ('notified', 'urgent'):
                # Pedido en preparación
                picking.with_delay(priority=1).prepare_order_reception()
                picking.with_delay(priority=1).notify_user()
            if vals.get('date_done', False) and picking.state_papeur in ('notified', 'urgent'):
                # Pedido finalizado
                picking.cancel_order_urgent()
                picking.vstock_data.state_papeur = 'done'
                picking.with_delay(priority=1, eta=1800).auto_deliver_order()
                picking.with_delay(priority=1).ready_order()

        return res

    @api.multi
    def prepare_order(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/prepare_order'
        web_endpoint_reception = f'{ppu_endpoint}/notified'
        for picking in self:
            data = {
                "name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                "odoo_id": picking.id,
            }
            data_reception = {
                "name": f"{picking.origin or ''} - {picking.name}",
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
                response_reception = requests.post(web_endpoint_reception, json=data_reception)
                response.raise_for_status()
                response_reception.raise_for_status()
                picking.vstock_data.state_papeur = 'notified'
            except requests.exceptions.RequestException as e:
                raise UserError(_("Something went wrong: %s" % e))

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60})
    @api.multi
    def prepare_order_reception(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/doing'
        for picking in self:
            data = {
                "name": f"{picking.origin or ''} - {picking.name}",
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise UserError(_("Something went wrong: %s" % e))

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
                response.raise_for_status()
                picking.vstock_data.state_papeur = 'urgent'
            except requests.exceptions.RequestException as e:
                raise UserError(_("Something went wrong: %s" % e))

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
                response_reception = requests.post(web_endpoint_reception, json=data_reception)
                response.raise_for_status()
                response_reception.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise UserError(_("Something went wrong: %s" % e))
            picking.vstock_data.state_papeur = False

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
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise UserError(_("Something went wrong: %s" % e))

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60})
    @api.multi
    def ready_order(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/ready'
        for picking in self:
            data = {
                "name": f"{picking.origin or ''} - {picking.name}",
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise UserError(_("Something went wrong: %s" % e))

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60})
    @api.multi
    def notify_user(self):
        ppu_endpoint = self.env['ir.config_parameter'].sudo().get_param('papeur.url')
        web_endpoint = f'{ppu_endpoint}/assign_user'
        for picking in self:
            data = {
                "name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                "user": "Asignado",
                "odoo_id": picking.id
            }
            try:
                response = requests.post(web_endpoint, json=data)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise UserError(_("Something went wrong: %s" % e))

    @api.model
    def return_orders(self):
        pickings = self.env['stock.picking'].search([('state', '=', 'assigned'),
                                                     ('picking_type_code', '=', 'outgoing'),
                                                     ('state_papeur', '!=', False),
                                                     ('state_papeur', '!=', 'done')])

        orders = [{"name": f"{picking.id_vstock} - {picking.name} - {picking.origin or ''} - {picking.partner_id.commercial_partner_id.name}",
                   "odoo_id": picking.id,
                   "state": picking.state_papeur,
                   "user": picking.user_vstock} for picking in pickings]
        return orders

    @api.model
    def return_orders_reception(self):
        pickings = self.env['stock.picking'].search([('state', '=', 'assigned'),
                                                     ('picking_type_code', '=', 'outgoing'),
                                                     ('state_papeur', '!=', False),
                                                     ('state_papeur', '!=', 'done')])
        orders = [{"name": f"{picking.origin or ''} - {picking.name}",
                   "odoo_id": picking.id,
                   "state": picking.state_papeur,
                   "state_vstock": picking.state_vstock} for picking in pickings]
        return orders

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60})
    @api.multi
    def auto_deliver_order(self):
        for pick in self:
            pick.deliver_order()
