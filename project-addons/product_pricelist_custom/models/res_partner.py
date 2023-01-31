from odoo import models,api,fields,_
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"


    pricelist_brand_ids = fields.Many2many('product.pricelist', domain=[('brand_group_id', '!=', False),
                                                                        ('base_pricelist', '=', False)])

    @api.constrains('pricelist_brand_ids')
    def _check_tags(self):
        for partner in self:
            brand_ids = set()
            for pricelist in partner.pricelist_brand_ids:
                if pricelist.brand_group_id.id in brand_ids:
                    raise ValidationError(
                        _("There is already a pricelist for %s in this partner." % pricelist.brand_group_id.name))
                else:
                    brand_ids.add(pricelist.brand_group_id.id)

