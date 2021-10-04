from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    captio_client_id = fields.Char(string='Captio Client Id')
    captio_client_secret = fields.Char(string='Captio Client Secret')
    captio_customer_key = fields.Char(String='Captio Customer Key')

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('captio.client_id', self.captio_client_id)
        ICPSudo.set_param('captio.client_secret', self.captio_client_secret)
        ICPSudo.set_param('captio.customer_key', self.captio_customer_key)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        res.update({
            'captio_client_id': ICPSudo.get_param(
                'captio.client_id', default=''),
            'captio_client_secret': ICPSudo.get_param(
                'captio.client_secret', default=''),
            'captio_customer_key': ICPSudo.get_param(
                'captio.customer_key', default=''),
        })
        return res