# -*- coding: utf-8 -*-
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


class product(models.Model):

    _inherit = "product.product"

    tag_ids = fields.Many2many(
            'product.tag',
            'product_tag_rel',
            'product_id',
            'tag_id',
            'Tags')


class product_tag(models.Model):

    @api.multi
    def name_get(self):
        reads = self.read(['name', 'parent_id'])
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id'] and record['parent_id'][1]:
                name = record['parent_id'][1] + u' / ' + (name or "")
            res.append((record['id'], (name or "")))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid,
                              [('name', operator, name)] + args,
                              limit=limit, context=context)
            ids = ids + self.search(cr, uid,
                                    [('parent_id', 'in', ids)] + args,
                                    limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    @api.multi
    @api.depends('name', 'parent_id')
    def _name_get_fnc(self):
        for record in self:
            record.complete_name = record.name_get()[0][1]

    _name = "product.tag"
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = "name"
    _order = 'parent_left'

    name = fields.Char('Name', size=64, required=True)
    complete_name = fields.Char(compute="_name_get_fnc", string='Name')
    product_ids = fields.Many2many(
            'product.product',
            'product_tag_rel',
            'tag_id',
            'product_id',
            'Products')
    parent_id = fields.Many2one('product.tag', 'Parent',
                                ondelete='cascade')
    child_id = fields.One2many('product.tag', 'parent_id',
                               string='Child tags')
    parent_left = fields.Integer('Left Parent', index=True)
    parent_right = fields.Integer('Right Parent', index=True)
