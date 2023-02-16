from odoo import models,api,fields,_
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"


    pricelist_brand_ids = fields.Many2many('product.pricelist', domain=[('brand_group_id', '!=', False),
                                                                        ('base_pricelist', '=', False)])

    @api.constrains('pricelist_brand_ids','team_id')
    def _check_tags(self):
        for partner in self:
            brand_ids = set()
            for pricelist in partner.pricelist_brand_ids:
                if pricelist.brand_group_id.id in brand_ids:
                    raise ValidationError(
                        _("There is already a pricelist for %s in this partner." % pricelist.brand_group_id.name))
                else:
                    brand_ids.add(pricelist.brand_group_id.id)
                if pricelist.team_id and partner.team_id and pricelist.team_id != partner.team_id :
                    raise ValidationError(
                        _("You cannot add a pricelist (%s) which sales team (%s) != partner sales team (%s)"
                          % (pricelist.name, pricelist.team_id.name,partner.team_id.name)))


    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        self.env['product.pricelist'].set_default_brand_pricelists(res)
        return res

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if vals.get("team_id") or vals.get("pricelist_brand_ids", False):
            self.env['product.pricelist'].set_default_brand_pricelists(self)
        return res

