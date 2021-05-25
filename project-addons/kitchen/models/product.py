from odoo import models, _, api, fields, exceptions


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    customization_type_ids = fields.Many2many('customization.type', string="Type")

    customizable = fields.Boolean()

    def create(self, vals):
        if vals.get('type','') == 'product':
            brand_id = vals.get("product_brand_id", False)
            category_id = vals.get("categ_id", False)
            rules = self.env['automatic.customization.type.rule'].search(
                ['&', '|', ('product_brand_id', '=', False), ('product_brand_id', '=', brand_id), '|',
                 ('product_categ_id', '=', False), ('product_categ_id', '=', category_id)])
            if rules:
                types_ids = rules.mapped('type_id').ids
                customization_types = vals.get("customization_type_ids", False)
                if customization_types:
                    # customization_types is a Many2many field, so the format is [(6,0,[Ids])]
                    types_ids += customization_types[0][2]
                vals["customizable"] = True
                vals["customization_type_ids"] = [(6, 0, types_ids)]
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        brand_id = vals.get("product_brand_id", False)
        category_id = vals.get("categ_id", False)
        type = vals.get("type", False)
        for product in self:
            if (brand_id or category_id) and ((not type and product.type=='product') or type=='product'):
                if not brand_id:
                    brand_id = product.product_brand_id.id
                else:
                    category_id = product.categ_id.id
                rules = self.env['automatic.customization.type.rule'].search(
                    ['&', '|', ('product_brand_id', '=', False), ('product_brand_id', '=', brand_id), '|',
                     ('product_categ_id', '=', False), ('product_categ_id', '=', category_id)])
                types_ids = []
                rules_old = self.env['automatic.customization.type.rule'].search(
                    ['&', '|', ('product_brand_id', '=', False), ('product_brand_id', '=', product.product_brand_id.id),
                     '|',
                     ('product_categ_id', '=', False), ('product_categ_id', '=', product.categ_id.id)])
                rules_to_remove = rules_old - rules
                if rules_to_remove:
                    types_to_remove = rules_to_remove.mapped('type_id')
                    types_ids += [x.id for x in product.customization_type_ids - types_to_remove]
                else:
                    types_ids += product.customization_type_ids.ids
                if rules:
                    types_ids += rules.mapped('type_id').ids
                vals["customizable"] = len(types_ids)>0
                vals["customization_type_ids"] = [(6, 0, types_ids)]
        return super(ProductTemplate, self).write(vals)
