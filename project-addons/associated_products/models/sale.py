##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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

from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _filter_lines_associated(self, lines):
        """
            Filter the order lines based on associated lines.
            :param lines: A dicc of order lines to update.
            :return new_lines: A filtered list of order lines.
        """
        ids_to_erase = set([x[1] for x in lines if x[0] == 2])
        new_lines = []
        new_lines_ids = set()
        dicc_modes = {'update': 1, 'remove': 2, 'remove_link': 3, 'add_link': 4}
        modes_values = dicc_modes.values()
        for line in lines:
            update_mode = line[0]
            line_id = line[1]
            if update_mode in modes_values:
                o_line = self.env['sale.order.line'].browse(line_id).exists()
                if not o_line or o_line.original_line_id.id in ids_to_erase:
                    continue
                if update_mode == dicc_modes['update']:
                    new_lines_ass, new_lines_ids_ass = o_line._reset_associated_lines(line)
                    new_lines.extend(new_lines_ass)
                    new_lines_ids.update(new_lines_ids_ass)
                    ids_to_erase.update(new_lines_ids_ass)
            if update_mode not in modes_values or line_id not in new_lines_ids:
                new_lines.append(line)
                new_lines_ids.add(line_id)
        return new_lines

    @api.multi
    def write(self, vals):
        """
        Override the write method to filter the order lines to update.
        :param vals: A dictionary containing the updated values.
        :return The result of the super().write() method.
        """
        lines = vals.get('order_line', False)
        if lines:
            new_lines = self._filter_lines_associated(lines)
            vals['order_line'] = new_lines
        return super().write(vals)


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    original_line_id = fields.Many2one('sale.order.line', "Origin", ondelete='cascade')
    assoc_line_ids = fields.One2many('sale.order.line', 'original_line_id', "Associated lines")

    def _reset_associated_lines(self, line):
        """
        Reset associated lines based on the update values of the line called from order write method.
        :param line: A dicc representing the update values of the line.
        :return new_lines: A list of new lines to be added to the order write values.
        :return ids_to_erase: A set of line IDs to be erased.
        """
        update_vals = line[2]
        ids_to_erase = set()
        new_lines=[]
        if 'product_id' in update_vals:
            for assoc in self.assoc_line_ids:
                assoc.reservation_ids.unlink()
                new_lines.append([2, assoc.id])
                ids_to_erase.add(assoc.id)
            self.add_associated_lines(self.env['product.product'].browse(update_vals['product_id']))
        return new_lines, ids_to_erase

    def _get_pricelist(self, product):
        """
        Determines the price list to be used in calculating the price of the new associated line based on the product brand.
        :param product: The product that determines the price list based on its brand
        :return: the pricelist calculated
        """
        pricelists = self.order_id.pricelist_brand_ids.filtered(
            lambda p: product.product_brand_id in p.brand_group_id.brand_ids)
        return pricelists.id if pricelists else self.order_id.pricelist_id.id

    def add_associated_lines(self, product):
        """
        Add associated lines to the current record based on the given product.
        :param product: The product for which associated lines are added.
        """
        fiscal_obj = self.env['account.fiscal.position']
        pricelist_obj = self.env['product.pricelist']
        for associated in product.associated_product_ids:
            qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            tax_ids = fiscal_obj.map_tax(associated.associated_id.taxes_id)
            pricelist = self._get_pricelist(product)
            price = pricelist_obj.price_get(associated.associated_id.id,
                                            associated.quantity * qty,
                                            self.order_id.partner_id.id)[pricelist]
            discount = associated.discount if associated.discount > self.discount else self.discount
            args_line = {
                'price_unit': price,
                'product_uom': associated.uom_id.id,
                'product_uom_qty': associated.quantity * qty,
                'product_id': associated.associated_id.id,
                'original_line_id': self.id,
                'customer_lead': associated.associated_id.sale_delay or 0.0,
                'tax_id': [(6, 0, tax_ids.ids)],
                'discount': discount,
                'route_id': self.route_id.id or False,
                'order_id':self.order_id.id,
                'sequence': self.sequence+1
            }
            new_line = self.create(args_line)
            new_line.product_id_change()


    @api.model
    def create(self, vals):
        """
        Override the create method to add associated lines.
        Creates a new record and adds associated lines.
        :return The newly created record.
        """
        product_obj = self.env['product.product']
        product_id = vals.get('product_id')
        res = super(SaleOrderLine, self).create(vals)
        if product_id and not self.env.context.get('not_associated', False):
            product = product_obj.browse(product_id)
            res.add_associated_lines(product)
        return res

    @api.multi
    def write(self,vals):
        """
        Override the write method to update associated line quantities.
        Updates the associated line quantities based on changes in the 'product_uom_qty' of the original line.
        :param vals: Dictionary of values to be written.
        :return Result of the super().write() method.
        """
        res = super().write(vals)
        if 'product_uom_qty' in vals:
            for line in self:
                for assoc_line in line.assoc_line_ids:
                    quantity = line.product_id.associated_product_ids.filtered(
                        lambda p: p.associated_id == assoc_line.product_id).quantity
                    assoc_line.product_uom_qty = line.product_uom_qty * quantity
        return res
