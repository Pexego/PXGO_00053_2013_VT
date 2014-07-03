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


class ui(orm.Model):

    _inherit = "product.product"

    _columns = {
        'state2': fields.selection([
            ('active', 'Active'),
            ('edition', 'In edition'),
            ('published', 'Published')], 'Status',
            readonly=True, required=True),
        }

    _defaults = {
        'state2': 'active',
        'sale_ok': False
    }

    def act_active(self, cr, uid, ids, context=None):
        return True
    def act_edition(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state2': 'edition'}, context)
        return True

    def act_publish(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state2': 'published', 'sale_ok': True}, context)
        return True

