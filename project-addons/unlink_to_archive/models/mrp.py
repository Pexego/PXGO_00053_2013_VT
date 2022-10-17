from odoo import models, api, fields

class MrpBom(models.Model):

    _inherit = 'mrp.bom'

    @api.multi
    def unlink(self):
        self.write({'active': False})

class MrpBomLine(models.Model):

    _inherit = 'mrp.bom.line'


    active = fields.Boolean('Active', default=True)

    @api.multi
    def unlink(self):
        self.write({'active':False})
