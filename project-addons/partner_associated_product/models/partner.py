
from odoo import fields, models, api,_


class Partner(models.Model):

    _inherit = 'res.partner'

    associated_product_ids = fields.One2many('res.partner.associated.product', 'partner_id', "Supplier Associated products")

    def partner_associated_products_action(self):
        return {
            'domain': "[('partner_id','=', " + str(self.id) + ")]",
            'name': _('Supplier Associated products'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'tree_view_ref': 'product_associated_tree_view', 'default_partner_id': self.id},
            'res_model': 'res.partner.associated.product',
            'type': 'ir.actions.act_window',
        }