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
from openerp.tools.translate import _


class res_partner(orm.Model):

    _inherit = "res.partner"

    _columns = {
        'prospective': fields.boolean('Prospective'),
        }

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=100):
        res = super(res_partner,self).name_search(cr, uid, name, args,
                                                  operator, context, limit)
        if context.get('show_prospective', False):
            context.pop('show_prospective', None)
            if not args:
                args = []
            args.append(('prospective', '=', True))
            args.append(('active', '=' , False))
            ids = self.pool.get('res.partner').search(cr, uid, args, context=context)
            names = self.name_get(cr, uid, ids, context)
            res += names
            if len(res) > limit:
                res = res[:limit]
        return res

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        res = super(res_partner,self).search(cr, user, args, offset, limit, order, context, count)
        if context is None:
            context = {}
        if context.get('show_prospective', False):
            context.pop('show_prospective', None)
            ids = self.search(cr, user, [('prospective', '=', 1), ('active', '=', 0)], offset, limit, order, context, count)
            res += ids
            if count:
                res += len(ids)
            if limit and len(res) > limit:
                res = res[:limit]
        return res


