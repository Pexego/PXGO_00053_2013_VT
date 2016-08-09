# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api
import time


class ResPartner(models.Model):

    _inherit = 'res.partner'

    discount = fields.Float('Discount', compute='_get_discount')

    @api.one
    def _get_discount(self):
        discount = 0.0
        if self.property_product_pricelist:
            pricelist = self.property_product_pricelist
            version = False
            date = time.strftime('%Y-%m-%d')
            date = date[0:10]
            for v in pricelist.version_id:
                if ((v.date_start is False) or (v.date_start <= date)) and \
                        ((v.date_end is False) or (v.date_end >= date)):
                    version = v
                    break
            if version:
                item = version.items_id[-1]
                if item:
                    discount = item.price_discount
            if discount < 0.0:
                self.discount = abs(discount) * 100
            else:
                self.discount = 0.0

    @api.model
    def create(self, vals):
        if vals.get('user_id', False) and 'web' in vals.keys() and vals['web']:
            user = self.env['res.users'].browse(vals['user_id'])
            if not user.web:
                user.web = True
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        delete = True
        for partner in self:
            if 'web' in vals.keys() and vals['web']:
                user_id = vals.get('user_id', False)
                if user_id:
                    user = self.env['res.users'].browse(user_id)
                else:
                    user = partner.user_id
                if user and not user.web:
                    user.web = True
                if partner.web != vals['web']:
                    delete = False
                if delete:
                    del vals['web']

        return super(ResPartner, self).write(vals)
