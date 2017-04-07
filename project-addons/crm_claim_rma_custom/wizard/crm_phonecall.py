# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Visiotech All Rights Reserved
#    $Jesús García Manzanas <jgmanzanas@visiotech.es>$
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

from openerp import models, api, fields, _
import datetime
from datetime import datetime

CALL_TYPE = [
                   ('check_stock', 'Check Stock'),
                   ('check_prices', 'Check Prices'),
                   ('order', 'Order/Budget'),
                   ('counsel', 'Counsel'),
                   ('shipment_status', 'Shipments status'),
                   ('rma_complain', 'RMA Complain/Claim'),
                   ('tech_complain', 'Tech Complain/Claim'),
                   ('web_complain', 'Web Complain/Claim'),
                   ('shipment_complain', 'Shipment Complain/Claim'),
                   ('accounting_complain', 'Accounting Complain/Claim'),
                   ]

class crm_phonecall(models.Model):
    """ Wizard for CRM phonecalls"""
    _inherit = "crm.phonecall"

    partner_id = fields.Many2one('res.partner', 'Contact', required=True)
    start_date = fields.Datetime('Start Date', readonly=True, default=fields.Datetime.now)
    name = fields.Text('Call Summary')
    user_id = fields.Many2one('res.users', 'Responsible', readonly=True)
    call_type = fields.Selection(CALL_TYPE,'Call type', required=True)

    @api.multi
    def end_call(self):
        self.ensure_one()
        duration = datetime.now() - datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')

        datas = {
            'model': 'crm.phonecall',
            'create_date': self.start_date,
            'date': self.start_date,
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'name': self.name or False,
            'categ_id': False,
            'section_id': False,
            'opportunity_id': False,
            'duration': (duration.seconds / float(60)),
            'state': 'done',
            'call_type': self.call_type
        }
        super(crm_phonecall, self).write(datas)
