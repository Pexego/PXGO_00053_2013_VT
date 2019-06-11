from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    url_policy = fields.Text(string="web privacy_policy", default='https://www.visiotechsecurity.com/en/legal-notice-and-the-privacy-policy',
                             help="link to the privacy policy", translate=True)
    url_profile = fields.Text(string="web profile", default='https://www.visiotechsecurity.com/en/login/profile',
                              help="link to the profile in the web", translate=True)
    url_products = fields.Text(string="web products", default='https://www.visiotechsecurity.com/en/',
                               help="link to section products", translate=True)
    url_contact = fields.Text(string="contact number", default='63625481',
                               help="Number contact depend on the country", translate=True)
