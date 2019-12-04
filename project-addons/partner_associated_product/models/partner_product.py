
from odoo import fields, models, api


class PartnerAssociatedProducts(models.Model):

    _name = 'res.partner.associated.product'
    _description = "This model provides the association between a partner and their associated products"

    partner_id = fields.Many2one('res.partner', "Partner", required=True)
    product_id = fields.Many2one('product.product', "Product", required=True)
    price_unit = fields.Float("Price per Unit",default=0,required=True)
    qty = fields.Integer("Quantity",default=0,required=True)
    discount = fields.Float("Discount",default=0.0,required=True)

    @api.model
    def create(self,vals):
        vals['partner_id']=self.env.context['active_id']
        return super(PartnerAssociatedProducts, self).create(vals)



