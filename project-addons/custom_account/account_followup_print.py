# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, api, _


class AccountFollowupPrint(models.Model):
    _inherit = 'account_followup.print'

    """
    Funcion para automatizar el envio de correos cada dia.
    Es la misma funcion que do_process de account_followup.print
    pero modificando la fecha por la fecha de hoy
    """
    def automatice_process(self, cr, uid, ids, context=None):
        context = dict(context or {})

        # Get partners
        tmp = self._get_partners_followp(cr, uid, ids, context=context)
        partner_list = tmp['partner_ids']
        to_update = tmp['to_update']
        date = fields.Date.today()
        data = self.read(cr, uid, ids, context=context)[0]
        data['followup_id'] = data['followup_id'][0]

        # Update partners
        self.do_update_followup_level(cr, uid, to_update, partner_list, date, context=context)
        # process the partners (send mails...)
        restot_context = context.copy()
        restot = self.process_partners(cr, uid, partner_list, data, context=restot_context)
        context.update(restot_context)
        # clear the manual actions if nothing is due anymore
        nbactionscleared = self.clear_manual_actions(cr, uid, partner_list, context=context)
        if nbactionscleared > 0:
            restot['resulttext'] = restot['resulttext'] + "<li>" + _(
                "%s partners have no credits and as such the action is cleared") % (str(nbactionscleared)) + "</li>"
            # return the next action
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'),
                                                  ('name', '=', 'view_account_followup_sending_results')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        context.update(
            {'description': restot['resulttext'], 'needprinting': restot['needprinting'], 'report_data': restot['action']})
        return {
            'name': _('Send Letters and Emails: Actions Summary'),
            'view_type': 'form',
            'context': context,
            'view_mode': 'tree,form',
            'res_model': 'account_followup.sending.results',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
    }
