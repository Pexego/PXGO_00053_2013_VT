# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ProductBrand(models.Model):

    _inherit = 'product.brand'

    code = fields.Char('Internal code')
    not_compute_joking = fields.Boolean('Not compute joking index')


class ProductCategory(models.Model):

    _inherit = 'product.category'

    code = fields.Char('Internal code')


class ProductTag(models.Model):

    _inherit = 'product.tag'

    def _get_tag_recursivity(self):
        tags = []
        tagsa = []
        tagsb = []

        for t in self:
            tagsb.append(t.name)
            if t.parent_id:
                tagsa = t.parent_id._get_tag_recursivity([t.parent_id.id])
                if tagsa:
                    tags = list(set(tagsa + tagsb))
        if tags:
            return tags
        else:
            return tagsb
