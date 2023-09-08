from odoo import _, api, fields, models

class ViewPrices(models.TransientModel):
    _name = 'view.prices'

    table_item_ids = fields.Many2many('product.pricelist.item', readonly=True,
                                domain=[('pricelist_id.active', '=', True), ('pricelist_id.base_pricelist', '=', True),
                                        '|', ('pricelist_calculated', '=', False),
                                        ('pricelist_calculated.brand_group_id', '=', False)]
                                )
    table_item_brand_ids = fields.Many2many('product.pricelist.item', readonly=True,
                                 domain=['&', '|', '&', ('pricelist_id', '=', False),
                                         ('pricelist_calculated.brand_group_id', '!=', False),
                                         ('brand_group_id', '!=', False), ('pricelist_calculated', '!=', False)])

    default_code = fields.Char(readonly=True)
