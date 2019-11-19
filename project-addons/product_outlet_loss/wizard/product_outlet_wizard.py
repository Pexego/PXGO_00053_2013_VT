##############################################################################
#
#    Copyright (C) 2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
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

from odoo import models, fields, api, exceptions, _
from datetime import datetime, time
from odoo.exceptions import ValidationError


class ProductOutletWizard(models.TransientModel):
    _inherit = 'product.outlet.wizard'

    price_unit = fields.Float(
        'Price PVPA',
        default=lambda self: self.env['product.product'].browse(
        self.env.context.get('active_id', False)).list_price1, Readonly=True)

    commercial_cost = fields.Float(
        'Commercial Cost',
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).commercial_cost)

    percent = fields.Char('Default Outlet Price in %', default=lambda self: self.env['product.product'].browse(
        self.env.context.get('active_id', False)).company_id.outlet_per_cent, Readonly=True)

    qty_available = fields.Float(
        'Qty from stock',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)).qty_available, Readonly=True)

    date_move = fields.Date('Move to outlet on', default=fields.datetime.now())

    @api.multi
    def make_move(self):
        ctx = dict(self.env.context)
        ctx['warehouse_id'] = self.warehouse_id.id
        ctx['location'] = self.location_orig_id.id

        if self.state == "first":
            res = super(ProductOutletWizard, self).make_move()
        else:
            if self.product_id.with_context({'location': self.location_orig_id.id, 'warehouse': self.warehouse_id.id}).qty_available < self.qty:
                raise ValidationError(_("Qty to outlet must be <= qty available on the location"))
            if self.qty <= 0:
                raise ValidationError(_("Qty to outlet must be >=0"))
            category_selected = self.env['product.category'].browse(int(self.categ_id))
            outlet_product_selected = self.env['product.product'].search(
                [('default_code', '=', self.product_id.name + category_selected.name)]
            )

            res = super(ProductOutletWizard, self).make_move()

            if self.state == "last":
                outlet_product = self.env['product.product'].search(
                    [('normal_product_id', '=', self.product_id.id), ('categ_id', '=', int(self.categ_id))])

                values = {
                    'qty': self.qty,
                    'price_unit': self.product_id.list_price1,
                    'price_outlet': self.product_id.list_price1 * (1 - (category_selected.percent / 100)),
                    'product_id': outlet_product.id,
                    'date_move': self.date_move,
                    'outlet_ok': True
                }
                self.env['outlet.loss'].create(values)

                if not outlet_product_selected:
                    for item in outlet_product.item_ids:
                        item.fixed_price = self.product_id.with_context(pricelist=item.pricelist_id.id).price * \
                                                            (1 - (category_selected.percent / 100))
                    standard_price_outlet = self.product_id.standard_price * (1 - (category_selected.percent / 100))
                    standard_price_outlet_2 = self.product_id.standard_price_2 * (1 - (category_selected.percent / 100))
                    list_updated_price = outlet_product.get_list_updated_prices()
                    values = {
                        'standard_price': standard_price_outlet,
                        'standard_price_2': standard_price_outlet_2,
                        'commercial_cost': self.commercial_cost,
                        'list_price1':list_updated_price['list_price1'],
                        'list_price2': list_updated_price['list_price2'],
                        'list_price3': list_updated_price['list_price3'],
                        'list_price4': list_updated_price['list_price4'],
                        'pvd1_price': list_updated_price['pvd1_price'],
                        'pvd2_price': list_updated_price['pvd2_price'],
                        'pvd3_price': list_updated_price['pvd3_price'],
                        'pvd4_price': list_updated_price['pvd4_price'],
                        'pvi1_price': list_updated_price['pvi1_price'],
                        'pvi2_price': list_updated_price['pvi2_price'],
                        'pvi3_price': list_updated_price['pvi3_price'],
                        'pvi4_price': list_updated_price['pvi4_price'],
                        'pvm1_price': list_updated_price['pvm1_price'],
                        'pvm2_price': list_updated_price['pvm2_price'],
                        'pvm3_price': list_updated_price['pvm3_price']
                    }
                    outlet_product.write(values)

        return res
