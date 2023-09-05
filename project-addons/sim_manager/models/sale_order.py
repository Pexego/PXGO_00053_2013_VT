from odoo import models, api, _, exceptions, fields
import requests
import json


class SaleOrder(models.Model):

    _inherit = "sale.order"

    allow_sale_sim = fields.Boolean("Allow SIM", copy=False)

    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            products_sims = self.env['sim.type'].search([]).mapped('product_id')
            if any(line.product_id.id in products_sims.mapped('id') for line in sale.order_line):

                web_invoice_endpoint = self.env['ir.config_parameter'].sudo().get_param('web.sim.limit.endpoint')
                api_key = self.env['ir.config_parameter'].sudo().get_param('web.sim.invoice.endpoint.key')
                sim_active_limit = self.env['ir.config_parameter'].sudo().get_param('web.sim.active.limit')
                c_code = self.env.user.company_id.country_id.code

                headers = {'x-api-key': api_key,
                           'Content-Type': 'application/json'}
                data = {
                    "limit": int(sim_active_limit),
                    "odoo_id": sale.partner_id.id,
                    "origin": c_code.lower()
                }
                response = requests.put(web_invoice_endpoint, headers=headers, data=json.dumps(data))
                if response.status_code == 200:
                    info = json.loads(response.text)
                    if not info['access'] and not sale.allow_sale_sim:
                        raise exceptions.UserError(_("Order block, the client has too many sims inactive. {}% Active").format(int(info['percentage'])))
        return res
