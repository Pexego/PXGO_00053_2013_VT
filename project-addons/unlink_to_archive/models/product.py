from odoo import models,api,fields


class AssociatedProducts(models.Model):

    _inherit = 'product.associated'

    active = fields.Boolean('Active', default=True)

    @api.multi
    def unlink(self):
        self.write({'active': False})

