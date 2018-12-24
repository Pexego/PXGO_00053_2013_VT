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

from odoo import models, api


class sale_order(models.Model):

    _inherit = 'sale.order'

    def action_risk_approval(self, cr, uid, ids, context=None):
        order = self.browse(cr, uid, ids[0], context)
        view_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_custom', 'sale_confirm_wizard_form_wizard')
        wzd = self.pool('sale.confirm.wizard').create(cr, uid, {})

        self.apply_promotions(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'risk_approval'}, context)

        self.action_button_confirm(cr, uid, ids, context)

        if not order.is_all_reserved and 'confirmed' not in context:
            return {'name': "Sale confirm",
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'sale.confirm.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'res_id': wzd,
                    'views': [(view_form[1], 'form')]
                    }
        else:
            return True
