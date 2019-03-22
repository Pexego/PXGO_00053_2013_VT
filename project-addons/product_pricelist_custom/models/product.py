##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class ProductPricelist(models.Model):

    _inherit = 'product.pricelist'

    pricelist_compare_default = fields.Many2one('product.pricelist', "Pricelist to compare")
    base_pricelist = fields.Boolean("Pricelist base?")  # Marcar en tarifas PVD's y PVI's


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'

    pricelist_to_compare = fields.Many2one('product.pricelist', string="Compare to")
    # PVP's para los PVD's y PVD's para los PVI's
    pricelist_to_compare_price = fields.Float("Price pricelist compared", compute='_get_pricelist_to_compare_price')
    relation = fields.Float("Relation (%)", compute='_get_relation', store=True)
    margin = fields.Float("Margin (%)", compute='_get_relation', readonly=True, store=True)

    @api.multi
    @api.depends('fixed_price')
    def _get_pricelist_to_compare_price(self):
        for item in self:
            #product_id = item.product_id or self._origin and self._origin.product_id
            product_id = item.product_tmpl_id or item.product_id.product_tmpl_id
            if product_id and item.pricelist_to_compare and not item.pricelist_to_compare.base_pricelist:
                rule = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', item.pricelist_to_compare.id),
                    ('applied_on', '=', '3_global')])
                if rule and rule.base == 'pricelist' and rule.base_pricelist_id:
                    item.pricelist_to_compare_price = item.fixed_price * (1 - rule.price_discount / 100)

    @api.multi
    @api.depends('fixed_price')
    def _get_relation(self):
        for item in self:
            #product_id = item.product_id or self._origin and self._origin.product_id
            product_id = item.product_tmpl_id or item.product_id.product_tmpl_id
            if product_id:
                if item.fixed_price:
                    if item.pricelist_to_compare:
                        price_to_compare = item.fixed_price
                        if item.pricelist_to_compare.base_pricelist:
                            pricelist_to_compare = item.search([('pricelist_id', '=', item.pricelist_to_compare.id),
                                                                ('product_tmpl_id', '=', product_id.id)])
                            if pricelist_to_compare:
                                price_to_compare = pricelist_to_compare[0].fixed_price
                        else:
                            price_to_compare = item.pricelist_to_compare_price
                        item.relation = ((item.fixed_price - price_to_compare) / item.fixed_price) * 100
                    else:
                        item.relation = 0
                    item.margin = (1 - (product_id.standard_price / item.fixed_price)) * 100.0
                else:
                    item.relation = 0
                    item.margin = 0


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    @api.depends('item_ids.fixed_price')
    def _get_margins_relation(self):
        for prod in self:
            prod.relation_pvd_pvi_a = fields.Datetime.from_string(fields.Datetime.now()).second

    relation_pvd_pvi_a = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI 1 margin',
                                      digits=(5, 2), readonly=True)

    @api.model
    def create(self, vals):
        product_id = super().create(vals)
        base_pricelists = self.env['product.pricelist'].search([('base_pricelist', '=', True)],
                                                               order='sequence asc, id asc')

        items = []
        for pricelist in base_pricelists:
            items.append((0, 0, {'pricelist_id': pricelist.id,
                                 'pricelist_to_compare': pricelist.pricelist_compare_default and
                                                         pricelist.pricelist_compare_default.id or False,
                                 'product_id': product_id.id}))

        product_id.write({'item_ids': items})
        return product_id


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    relation_pvd_pvi_a = fields.\
        Float(related="product_variant_ids.relation_pvd_pvi_a", readonly=True)

