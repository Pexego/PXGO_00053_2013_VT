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

from openerp.osv import fields, orm


class product(orm.Model):

    _inherit = "product.product"

    _columns = {
        'tag_ids': fields.many2many(
            'product.tag',
            'product_tag_rel',
            'product_id',
            'tag_id',
            'Tags'),
    }


class product_tag(orm.Model):

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'parent_id'], context=context)
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

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _name = "product.tag"
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = "name"
    _order = 'parent_left'

    _columns = {
        'name': fields.char('Name', size=64),
        'complete_name': fields.function(_name_get_fnc, type="char",
                                         string='Name'),
        'product_ids': fields.many2many(
            'product.product',
            'product_tag_rel',
            'tag_id',
            'product_id',
            'Products'),
        'parent_id': fields.many2one('product.tag', 'Parent',
                                     ondelete='cascade'),
        'child_id': fields.one2many('product.tag', 'parent_id',
                                    string='Child tags'),
        'parent_left': fields.integer('Left Parent', select=True),
        'parent_right': fields.integer('Right Parent', select=True),
    }

    _constraints = [
        (orm.Model._check_recursion,
         'Error ! You cannot create recursive tags.', ['parent_id'])
    ]
