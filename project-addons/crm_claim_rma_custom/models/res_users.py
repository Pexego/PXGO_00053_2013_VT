from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_location = fields.Selection([('madrid1', 'Madrid - Vicálvaro'),
                                           ('italia', 'Italia - Arcore'),
                                           ('francia', 'Francia – Lyon'),
                                           ('portugal', 'Portugal – Lisboa'),
                                           ('transit', 'In transit')], "Warehouse Location")


class ResCompany(models.Model):
    _inherit = 'res.company'

    no_sync_picking = fields.Boolean("Not sync pickings", default=False)

