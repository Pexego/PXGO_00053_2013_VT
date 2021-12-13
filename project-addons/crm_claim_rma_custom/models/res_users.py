from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_location = fields.Selection([('madrid1', 'Madrid - Avd. del Sol'),
                                           ('madrid2', 'Madrid - Casablanca'),
                                           ('madrid3', 'Madrid - Vicálvaro'),
                                           ('italia', 'Italia - Arcore'),
                                           ('transit', 'In transit')], "Warehouse Location")
