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

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import re


class ProductPricelist(models.Model):

    _inherit = 'product.pricelist'

    pricelist_related_default = fields.Many2one('product.pricelist', "Default Related Pricelist")
    # This check allows you to add pricelist to product item_ids field(Check on PVD's y PVI's and Brand pricelists base)
    base_pricelist = fields.Boolean("Pricelist base")
    brand_group_id = fields.Many2one("brand.group")

    display_name = fields.Char(
        compute='_compute_display_name',
        string='Display Name', store=True, readonly=True)

    @api.multi
    @api.depends('name', 'brand_group_id')
    def _compute_display_name(self):
        for pricelist in self:
            display_name = pricelist.name
            if pricelist.brand_group_id:
                display_name = f"{pricelist.brand_group_id.name} / {pricelist.name}"
            pricelist.display_name = display_name

    def _compute_price_rule_get_items(self, products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids):
        """ This method overwrite _compute_price_rule_get_items of product module to add brand filtering
            :param products_qty_partner: list of tuples products, quantity, partner
            :param date: validity date
            :param uom_id: intermediate unit of measure (ID)
            :param prod_tmpl_ids: list of product.template
            :param prod_ids: list of product.product
            :param categ_ids: list of product.category
            :return: suitable product.pricelist.items for params conditions
        """
        self.ensure_one()
        product_tmpls = self.env["product.template"].browse(prod_tmpl_ids)
        brand_ids = product_tmpls.mapped("product_brand_id").ids
        self.env.cr.execute(
            """
            SELECT
                item.id
            FROM
                product_pricelist_item AS item
            LEFT JOIN product_category AS categ ON item.categ_id = categ.id
            LEFT JOIN product_brand AS brand ON item.product_brand_id = brand.id
            WHERE
                (item.product_tmpl_id IS NULL OR item.product_tmpl_id = any(%s))
                AND (item.product_id IS NULL OR item.product_id = any(%s))
                AND (item.categ_id IS NULL OR item.categ_id = any(%s))
                AND (item.product_brand_id IS NULL OR item.product_brand_id = any(%s))
                AND (item.pricelist_id = %s)
                AND (item.date_start IS NULL OR item.date_start<=%s)
                AND (item.date_end IS NULL OR item.date_end>=%s)
            ORDER BY
                item.applied_on, item.min_quantity desc, categ.parent_left desc
            """,
            (prod_tmpl_ids, prod_ids, categ_ids, brand_ids, self.id, date, date))

        item_ids = [x[0] for x in self.env.cr.fetchall()]
        return self.env['product.pricelist.item'].browse(item_ids)

    @api.multi
    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """ This method extends _compute_price_rule of product module to add extra discounts
            :param products_qty_partner: list of tuples products, quantity, partner
            :param date: validity date
            :param uom_id: intermediate unit of measure (ID)
            :return: dict{product_id: (price, suitable_rule) for the given pricelist}
        """
        res = super()._compute_price_rule(products_qty_partner, date, uom_id)
        for product_id, (price, rule_id) in res.items():
            rule = self.env['product.pricelist.item'].browse(rule_id)
            if price is not False and rule.price_extra_discounts:
                discounts = eval(rule.price_extra_discounts)
                if isinstance(discounts, (int, float)):
                    new_price = price - (price * (discounts / 100))
                else:
                    new_price = price
                    for discount in discounts:
                        new_price = new_price - (new_price * (discount / 100))
                res[product_id] = (new_price, rule_id)
        return res
    def get_base_brand_pricelists(self, product_brand_id):
        """ This method allows to search base pricelists of a specified brand
            :param product_brand_id: brand of a product (ID)
            :return: list of product.pricelist
        """
        return self.env['product.pricelist'].search([('base_pricelist', '=', True),
                ('brand_group_id', '!=', False),
                ('brand_group_id.brand_ids', '=',
                 product_brand_id)],
               order='sequence asc, id asc')

    def create_base_pricelist_items(self, product_id):
        """ This method allows to create pricelists for a specified product
            :param product_id:product.product (object)
        """
        items = []
        for pricelist in self:
            items.append((0, 0, {'pricelist_id': pricelist.id,
                                 'pricelist_calculated': pricelist.pricelist_related_default and
                                                         pricelist.pricelist_related_default.id or False,
                                 'product_id': product_id.id,
                                 'applied_on': '1_product'}))
        product_id.write({'item_ids': items})


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'

    pricelist_calculated = fields.Many2one('product.pricelist', string="Calculated Pricelist")
    pricelist_calculated_price = fields.Float("Price calculated", compute='_get_pricelist_calculated_price')
    margin = fields.Float("Margin (%)", compute='_get_margin', readonly=True, store=True)
    name_pricelist = fields.Char(related='pricelist_id.name', readonly=True)
    base = fields.Selection(selection_add=[('standard_price_2_inc', 'Cost 2')])
    pricelist_sequence = fields.Integer(related='pricelist_id.sequence', readonly=True)
    pricelist_calculated_sequence = fields.Integer(related='pricelist_calculated.sequence', readonly=True)
    calculated_brand_group_id = fields.Many2one(related="pricelist_calculated.brand_group_id")
    brand_group_id = fields.Many2one(related="pricelist_id.brand_group_id")
    item_id = fields.Many2one('product.pricelist.item')
    item_ids = fields.One2many(
        comodel_name='product.pricelist.item',
        inverse_name='item_id',
        string='Associated Items',
        required=False)
    applied_on = fields.Selection(selection_add=[('25_product_brand','Product Brand')])
    product_brand_id = fields.Many2one(
        comodel_name="product.brand",
        string="Brand",
        ondelete="cascade",
        help="Specify a brand if this rule only applies to products"
        "belonging to this brand. Keep empty otherwise.",
    )
    price_extra_discounts = fields.Char('Price Extra Discounts',
                                        help="This field can be a number(int or float) or a list of them separated by commas.",
                                        default="0")

    @api.constrains('price_extra_discounts')
    def _check_price_extra_discounts(self):
        """ This method check if the values in price_extra_discounts field have right format
            (number(float or int) or list of numbers)
        :return: ValidationError if the format is not correct
        """
        for item in self:
            matched = re.match('^[0-9]+(\.[0-9]+)?(,[0-9]+)*$', item.price_extra_discounts)
            if matched:
                discounts = eval(item.price_extra_discounts)
                if isinstance(discounts, (int, float)) or all([x for x in discounts if (isinstance(x, (int, float)))]):
                    return
            raise ValidationError(_("The pricelist item %s does not comply with the format of extra discounts."
                                    "It should be a number (integer or float) or a list of them separated by commas.")
                                  % item.name)

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        """ This method extend original method to restore state
            of product_brand_id field when applied_on change to another value
        """
        super()._onchange_applied_on()
        if self.applied_on != '25_product_brand':
            self.product_brand_id = False

    @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price',
                 'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge','product_brand_id',
                 'price_extra_discounts')
    def _get_pricelist_item_name_price(self):
        """ This method extend original method to assign brand name in the name of the item and formatting
        the price name when it has extra discounts"""
        super()._get_pricelist_item_name_price()
        for item in self:
            if item.product_brand_id:
                item.name = _("Brand: %s") % item.product_brand_id.name
            if item.price_extra_discounts:
                discounts = eval(item.price_extra_discounts)
                if isinstance(discounts, (int, float)):
                    discounts_formatted = discounts
                else:
                    discounts_formatted = ','.join(f' {discount} %' for discount in discounts)
                item.price = _("%s; %s of extra discounts") %(item.price,discounts_formatted)

    @api.multi
    def write(self, vals):
        """ This method writes the same values to the associated items and writes its calculated price
         to fixed_price in case it does not have a fixed price and is a calculated item without a base pricelist.
        :param vals: values to change
        :return: super()
        """
        res = super().write(vals)
        for item in self:
            if item.item_ids:
                item.item_ids.write(vals)
            elif 'fixed_price' not in vals and not item.base_pricelist_id and not item.pricelist_id and item.pricelist_calculated:
                item.fixed_price = item.pricelist_calculated_price
        return res

    @api.multi
    @api.depends('fixed_price')
    def _get_pricelist_calculated_price(self):
        """ This method compute the calculated price of a pricelist item."""
        for item in self:
            product_id = item.product_tmpl_id or item.product_id.product_tmpl_id
            if product_id and item.pricelist_calculated and not item.pricelist_calculated.base_pricelist:
                rule = self.env['product.pricelist.item'].search([
                    '&', ('pricelist_id', '=', item.pricelist_calculated.id), '|',
                    ('applied_on', '=', '3_global'), '|', '&', ('applied_on', '=', '2_product_category'),
                    ('categ_id', '=', product_id.categ_id.id),
                    '&', ('applied_on', '=', '25_product_brand'),
                    ('product_brand_id', '=', item.product_id.product_brand_id.id)])
                if rule:
                    if rule.base == 'pricelist' and rule.base_pricelist_id:
                        item.pricelist_calculated_price = item.fixed_price * (1 - rule.price_discount / 100)
                    elif rule.base == 'standard_price' or \
                            (rule.base == 'standard_price_2_inc' and not product_id.product_variant_id.standard_price_2_inc):
                        item.pricelist_calculated_price = product_id.standard_price * (1 - rule.price_discount / 100)
                    elif rule.base == 'standard_price_2_inc':
                        item.pricelist_calculated_price = product_id.product_variant_id.standard_price_2_inc * (1 - rule.price_discount / 100)
                    if rule.price_extra_discounts:
                        discounts = eval(rule.price_extra_discounts)
                        price= item.pricelist_calculated_price
                        if isinstance(discounts, (int, float)):
                            new_price = price - (price * (discounts / 100))
                        else:
                            new_price = price
                            for discount in discounts:
                                new_price = new_price - (new_price * (discount / 100))
                        item.pricelist_calculated_price = new_price

    @api.multi
    @api.depends('fixed_price', 'product_id.standard_price_2', 'product_tmpl_id.standard_price_2', 'product_id.standard_price_2_inc')
    def _get_margin(self):
        for item in self:
            product_id = item.product_tmpl_id or item.product_id.product_tmpl_id
            if product_id:
                if item.fixed_price:
                    item.margin = (1 - (product_id.product_variant_id.standard_price_2_inc / item.fixed_price)) * 100.0
                else:
                    item.margin = 0

    def get_brand_pricelist_items(self,brand_id):
        return self.env['product.pricelist.item'].search([('brand_group_id', '!=', False),
                                                          ('brand_group_id.brand_ids', '=', brand_id),
                                                          ('compute_price', '=', 'formula'),
                                                          ('product_brand_id', '=',brand_id)],
                                                         order='id asc')

class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    @api.depends('item_ids.fixed_price')
    def _get_margins_relation(self):
        for prod in self:
            # Update A pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: i.pricelist_id.name.endswith('Iberia')).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_a = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_a = 0
            # Update B pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: i.pricelist_id.name.endswith('Europa')).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_b = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_b = 0

            # Update C pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: i.pricelist_id.name.endswith('Italia')).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_c = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_c = 0

            # Update D pricelist relation
            pricelist_rel = prod.item_ids.filtered(lambda i: i.pricelist_id.name.endswith('Francia')).\
                sorted(key=lambda i: i.pricelist_id.sequence)
            if len(pricelist_rel) == 2 and pricelist_rel[0].fixed_price and pricelist_rel[1].fixed_price:
                prod.relation_pvd_pvi_d = ((pricelist_rel[0].fixed_price - pricelist_rel[1].fixed_price)
                                           / pricelist_rel[0].fixed_price) * 100
            else:
                prod.relation_pvd_pvi_d = 0


    @api.multi
    def get_product_price_with_pricelist(self, pricelist_name):
        pricelist = self.env['product.pricelist'].search([('name', '=', pricelist_name)])
        price = 0
        for product in self:
            if pricelist:
                price_items = self.env['product.pricelist.item'].search([('product_id', '=', product.id)])
                if pricelist.base_pricelist:
                    item = price_items.filtered(lambda x: x.pricelist_id.id == pricelist.id)
                    if item:
                        price = round(item.fixed_price, 2)
                else:
                    item = price_items.filtered(lambda x: x.pricelist_calculated.id == pricelist.id)
                    if item:
                        price = round(item.pricelist_calculated_price, 2)
            return price

    @api.multi
    def get_list_updated_prices(self):
        prices = {
            'list_price1': self.get_product_price_with_pricelist('PVPIberia'),
            'list_price2': self.get_product_price_with_pricelist('PVPEuropa'),
            'list_price3': self.get_product_price_with_pricelist('PVPItalia'),
            'list_price4': self.get_product_price_with_pricelist('PVPFrancia'),
            'pvd1_price': self.get_product_price_with_pricelist('PVDIberia'),
            'pvd2_price': self.get_product_price_with_pricelist('PVDEuropa'),
            'pvd3_price': self.get_product_price_with_pricelist('PVDItalia'),
            'pvd4_price': self.get_product_price_with_pricelist('PVDFrancia'),
            'pvi1_price': self.get_product_price_with_pricelist('PVIIberia'),
            'pvi2_price': self.get_product_price_with_pricelist('PVIEuropa'),
            'pvi3_price': self.get_product_price_with_pricelist('PVIItalia'),
            'pvi4_price': self.get_product_price_with_pricelist('PVIFrancia'),
            'pvm1_price': self.get_product_price_with_pricelist('PVMA'),
            'pvm2_price': self.get_product_price_with_pricelist('PVMB'),
            'pvm3_price': self.get_product_price_with_pricelist('PVMC')
            }
        return prices

    relation_pvd_pvi_a = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI Iberia relation',
                                      digits=(5, 2), readonly=True)
    relation_pvd_pvi_b = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI Europe relation',
                                      digits=(5, 2), readonly=True)
    relation_pvd_pvi_c = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI Italy relation',
                                      digits=(5, 2), readonly=True)
    relation_pvd_pvi_d = fields.Float(compute='_get_margins_relation',
                                      string='PVD/PVI France relation',
                                      digits=(5, 2), readonly=True)

    def create_brand_pricelist_items(self, brand_id):
        """ This method allows to create pricelists of a specified brand
            :param brand_id: brand of a product (ID)
        """
        for product_id in self:
            brand_pricelist_items = self.env['product.pricelist.item'].get_brand_pricelist_items(brand_id)
            items = []
            for item in brand_pricelist_items:
                real_item = product_id.item_ids.filtered(lambda i: i.pricelist_id == item.base_pricelist_id)
                items.append((0, 0, {'pricelist_id': item.base_pricelist_id.id,
                                                           'pricelist_calculated': item.pricelist_id.id,
                                                           'product_id': product_id.id,
                                                           'applied_on': '1_product',
                                                           'item_id': real_item.id}))
            product_id.write({'item_ids': items})

    def create_product_pricelist_items(self,brand_id):
        """ This method allows to create pricelists of products
            :param brand_id: brand of products (ID)
        """
        for product_id in self:
            base_brand_pricelists = self.env['product.pricelist'].get_base_brand_pricelists(brand_id)
            if base_brand_pricelists:
                base_brand_pricelists.create_base_pricelist_items(product_id)
                product_id.create_brand_pricelist_items(brand_id)
            else:
                base_pricelists = self.env['product.pricelist'].search([('base_pricelist', '=', True),
                                                                        ('brand_group_id', '=', False)],
                                                                       order='sequence asc, id asc')
                base_pricelists.create_base_pricelist_items(product_id)
    @api.model
    def create(self, vals):
        """ This method create product pricelist if it has brand.
        :param vals: values to create product
        :return: super()
        """
        product_id = super().create(vals)
        if not self.env.context.get('sync_db', False):
            if product_id.product_brand_id:
                product_id.create_product_pricelist_items(product_id.product_brand_id.id)
        return product_id

    @api.multi
    def write(self, vals):
        """ This method create/unlink product pricelists if the brand changes.
        :param vals: values to write product
        :return: super()
        """
        brand = vals.get('product_brand_id', False)
        for product in self:
            if brand and product.product_brand_id.id != brand:
                if product.item_brand_ids:
                    product.item_ids.unlink()
                    product.item_brand_ids.unlink()
                    product.create_product_pricelist_items(brand)
                else:
                    brand_pricelist_items = self.env['product.pricelist.item'].get_brand_pricelist_items(brand)
                    if brand_pricelist_items:
                        product.item_ids.unlink()
                        product.create_product_pricelist_items(brand)
        res = super().write(vals)
        if 'item_ids' in vals:
            prices_to_update = self.get_list_updated_prices()
            res = super().write(prices_to_update)
        return res

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):
        res = super().price_compute(price_type,  uom=uom, currency=currency, company=company)
        if price_type == 'standard_price_2' and self.id in res and res[self.id] == 0:
            # If cost(2) is 0, recalculate price with cost(1)
            res = self.price_compute('standard_price', uom=uom, currency=currency, company=company)
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

    item_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id', 'Pricelist Items',
                           domain=[('pricelist_id.active', '=', True),('pricelist_id.base_pricelist', '=', True),
                                   '|',('pricelist_calculated', '=', False),('pricelist_calculated.brand_group_id','=',False)])

    item_brand_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id',
                                     domain=['&', '|', '&', ('pricelist_id', '=', False),
                                             ('pricelist_calculated.brand_group_id', '!=', False),
                                             ('brand_group_id', '!=', False), ('pricelist_calculated', '!=', False)])

class ProductBrand(models.Model):
    _inherit = 'product.brand'

    group_brand_id = fields.Many2one('brand.group', string='Brand Group')
