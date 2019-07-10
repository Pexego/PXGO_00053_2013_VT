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

    pricelist_related_default = fields.Many2one('product.pricelist', "Default Related Pricelist")
    base_pricelist = fields.Boolean("Pricelist base")  # Marcar en tarifas PVD's y PVI's


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'

    pricelist_calculated = fields.Many2one('product.pricelist', string="Calculated Pricelist")
    pricelist_calculated_price = fields.Float("Price calculated", compute='_get_pricelist_calculated_price')
    margin = fields.Float("Margin (%)", compute='_get_margin', readonly=True, store=True)
    name_pricelist = fields.Char(related='pricelist_id.name', readonly=True)

    @api.multi
    @api.depends('fixed_price')
    def _get_pricelist_calculated_price(self):
        for item in self:
            product_id = item.product_tmpl_id or item.product_id.product_tmpl_id
            if product_id and item.pricelist_calculated and not item.pricelist_calculated.base_pricelist:
                rule = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', item.pricelist_calculated.id),
                    ('applied_on', '=', '3_global')])
                if rule:
                    if rule.base == 'pricelist' and rule.base_pricelist_id:
                        item.pricelist_calculated_price = item.fixed_price * (1 - rule.price_discount / 100)
                    elif rule.base == 'standard_price':
                        item.pricelist_calculated_price = product_id.standard_price * (1 - rule.price_discount / 100)

    @api.multi
    @api.depends('fixed_price', 'product_id.standard_price_2')
    def _get_margin(self):
        for item in self:
            product_id = item.product_tmpl_id or item.product_id.product_tmpl_id
            if product_id:
                if item.fixed_price:
                    item.margin = (1 - (product_id.standard_price_2 / item.fixed_price)) * 100.0
                else:
                    item.margin = 0


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    @api.depends('item_ids.fixed_price')
    def _get_margins_relation(self):
        for prod in self:
            # Update A pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: 'A' == i.pricelist_id.name[-1:]).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_a = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_a = 0
            # Update B pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: 'B' == i.pricelist_id.name[-1:]).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_b = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_b = 0

            # Update C pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: 'C' == i.pricelist_id.name[-1:]).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_c = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_c = 0

            # Update D pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: 'D' == i.pricelist_id.name[-1:]).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_d = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_d = 0

    @api.multi
    def get_product_price_with_pricelist(self, pricelist_name):
        id_pricelist = self.env['product.pricelist'].search([('name', '=', pricelist_name)]).id
        for product in self:
            if id_pricelist:
                price = product.with_context(pricelist=id_pricelist).price
                price = round(price, 2)
            else:
                price = 0
            return price

    relation_pvd_pvi_a = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI A relation',
                                      digits=(5, 2), readonly=True)
    relation_pvd_pvi_b = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI B relation',
                                      digits=(5, 2), readonly=True)
    relation_pvd_pvi_c = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI C relation',
                                      digits=(5, 2), readonly=True)
    relation_pvd_pvi_d = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI D relation',
                                      digits=(5, 2), readonly=True)

    @api.model
    def create(self, vals):
        product_id = super().create(vals)
        base_pricelists = self.env['product.pricelist'].search([('base_pricelist', '=', True)],
                                                               order='sequence asc, id asc')

        items = []
        for pricelist in base_pricelists:
            items.append((0, 0, {'pricelist_id': pricelist.id,
                                 'pricelist_calculated': pricelist.pricelist_related_default and
                                                         pricelist.pricelist_related_default.id or False,
                                 'product_id': product_id.id}))

        product_id.write({'item_ids': items})
        return product_id

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'item_ids' in vals:
            prices = {
                'list_price1': self.get_product_price_with_pricelist('PVPA'),
                'list_price2': self.get_product_price_with_pricelist('PVPB'),
                'list_price3': self.get_product_price_with_pricelist('PVPC'),
                'list_price4': self.get_product_price_with_pricelist('PVPD'),
                'pvd1_price': self.get_product_price_with_pricelist('PVDA'),
                'pvd2_price': self.get_product_price_with_pricelist('PVDB'),
                'pvd3_price': self.get_product_price_with_pricelist('PVDC'),
                'pvd4_price': self.get_product_price_with_pricelist('PVDD'),
                'pvi1_price': self.get_product_price_with_pricelist('PVIA'),
                'pvi2_price': self.get_product_price_with_pricelist('PVIB'),
                'pvi3_price': self.get_product_price_with_pricelist('PVIC'),
                'pvi4_price': self.get_product_price_with_pricelist('PVID'),
                'pvm1_price': self.get_product_price_with_pricelist('PVMA'),
                'pvm2_price': self.get_product_price_with_pricelist('PVMB'),
                'pvm3_price': self.get_product_price_with_pricelist('PVMC')
            }
            res = super().write(prices)
        return res


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    relation_pvd_pvi_a = fields.\
        Float(related="product_variant_ids.relation_pvd_pvi_a", readonly=True)
    relation_pvd_pvi_b = fields. \
        Float(related="product_variant_ids.relation_pvd_pvi_b", readonly=True)
    relation_pvd_pvi_c = fields. \
        Float(related="product_variant_ids.relation_pvd_pvi_c", readonly=True)
    relation_pvd_pvi_d = fields. \
        Float(related="product_variant_ids.relation_pvd_pvi_d", readonly=True)

