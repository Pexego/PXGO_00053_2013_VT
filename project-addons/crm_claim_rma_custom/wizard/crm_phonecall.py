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

from openerp import models, api, fields
from datetime import datetime
import pytz

CALL_TYPE = [('check_stock', 'Check Stock'),
             ('check_prices', 'Check Prices'),
             ('order', 'Order/Budget'),
             ('counsel', 'Counsel'),
             ('shipment_status', 'Shipments status'),
             ('order_complain', 'Order Complain/Claim'),
             ('rma_complain', 'RMA Complain/Claim'),
             ('tech_complain', 'Tech Complain/Claim'),
             ('web_complain', 'Web Complain/Claim'),
             ('shipment_complain', 'Shipment Complain/Claim'),
             ('accounting_complain', 'Accounting Complain/Claim')]

CALL_TYPE_SAT = [('check_status_rma', 'Check RMA status'),
                 ('incidence_product', 'Incidence with product'),
                 ('check_working', 'Post-sale question on operation'),
                 ('counsel', 'Pre-sale query/advice'),
                 ('sat_complain', 'SAT Complaint/claim'),
                 ('ddns_registration', 'DDNS request for registration'),
                 ('check_courses', 'Enquiry about courses/certificates'),
                 ('others', 'Others')]

SCOPE = [('sales', 'Sales'),
         ('sat', 'SAT')]


class CrmPhonecall(models.Model):
    """ Wizard for CRM phonecalls"""
    _inherit = "crm.phonecall"

    local_tz = pytz.timezone('Europe/Madrid')

    name = fields.Char('Call Summary', readonly=True, default="/")
    partner_id = fields.Many2one('res.partner', 'Contact', required=True,
                                 domain=[['is_company', '=', 1],
                                         ['customer', '=', True]])
    start_date = fields.Datetime('Start Date', readonly=True,
                                 default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', 'Responsible', readonly=True)
    call_type = fields.Selection(CALL_TYPE, 'Call type', required=True)
    description = fields.Text('Call Description')
    partner_ref = fields.Char('Ref. Contact', readonly=True, compute='get_partner_ref')
    scope = fields.Selection(SCOPE, 'Scope call')
    call_type_sat = fields.Selection(CALL_TYPE_SAT, 'Call type', required=True)
    partner_country = fields.Many2one(related='partner_id.country_id', string='Country', readonly=True)
    brand_id = fields.Many2one('product.brand', 'Brand')

    def utc_to_local(self, utc_dt):
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(self.local_tz)
        return self.local_tz.normalize(local_dt)

    @api.one
    def get_partner_ref(self):
        if self.partner_id:
            self.partner_ref = self.partner_id.ref

    @api.multi
    def end_call(self):
        self.ensure_one()

        start_date = datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')
        final_start_date = datetime.\
            strptime(self.utc_to_local(start_date).
                     strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        format_start_date_all = datetime.strftime(final_start_date,
                                                  '%Y%m%d/%H%M')
        format_start_date = format_start_date_all.split('/')
        if self.name == "/":
            self.name = self.partner_id.ref + ' - ' + format_start_date[0] + \
                ' - ' + format_start_date[1]

        duration = datetime.now() - datetime.strptime(self.start_date,
                                                      '%Y-%m-%d %H:%M:%S')

        datas = {
            'model': 'crm.phonecall',
            'create_date': self.start_date,
            'date': self.start_date,
            'partner_id': self.partner_id.id,
            'partner_ref': self.partner_id.ref,
            'user_id': self.user_id.id,
            'name': self.name or False,
            'description': self.description or False,
            'categ_id': False,
            'section_id': False,
            'opportunity_id': False,
            'duration': (duration.seconds / float(60)),
            'state': 'done',
            'call_type': self.call_type,
            'call_type_sat': self.call_type_sat,
            'brand_id': self.brand_id.id
        }
        super(CrmPhonecall, self).write(datas)
