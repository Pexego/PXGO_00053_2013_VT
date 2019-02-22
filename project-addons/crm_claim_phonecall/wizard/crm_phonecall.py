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

from odoo import models, api, fields, exceptions, _
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError
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
             ('accounting_complain', 'Accounting Complain/Claim'),
             ('none', 'N/A')]

CALL_TYPE_SAT = [('check_status_rma', 'Check RMA status'),
                 ('incidence_product', 'Incidence with product'),
                 ('check_working', 'Post-sale question on operation'),
                 ('counsel', 'Pre-sale query/advice'),
                 ('sat_complain', 'SAT Complaint/claim'),
                 ('ddns_registration', 'DDNS request for registration'),
                 ('check_courses', 'Enquiry about courses/certificates'),
                 ('others', 'Others'),
                 ('none', 'N/A')]

SCOPE = [('sales', 'Sales'),
         ('sat', 'SAT')]


class CrmPhonecall(models.Model):
    """ Wizard for CRM phonecalls"""
    _inherit = 'crm.phonecall'

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
    partner_country = fields.Many2one('res.country', related='partner_id.country_id', string='Country', readonly=True)
    partner_salesperson = fields.Many2one('res.users', related='partner_id.user_id', string='Salesperson', readonly=True)
    brand_id = fields.Many2one('product.brand', 'Brand')
    subject = fields.Char('Call Subject')
    email_sent = fields.Boolean('Email sent', default=False, readonly=True)
    summary_id = fields.Many2one(comodel_name="crm.phonecall.summary",
                                 string="Summary",
                                 required=False,
                                 ondelete="restrict")

    def utc_to_local(self, utc_dt):
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(self.local_tz)
        return self.local_tz.normalize(local_dt)

    @api.multi
    def get_partner_ref(self):
        for call in self:
            if call.partner_id:
                call.partner_ref = call.partner_id.ref

    @api.model
    def create(self, datas):
        if 'call_type' not in datas:
            datas['call_type'] = 'none'
        if 'call_type_sat' not in datas:
            datas['call_type_sat'] = 'none'
        return super(CrmPhonecall, self).create(datas)

    @api.multi
    def write(self, datas):
        if not self.call_type and 'call_type' not in datas:
            datas['call_type'] = 'none'
        if not self.call_type_sat and 'call_type_sat' not in datas:
            datas['call_type_sat'] = 'none'
        return super(CrmPhonecall, self).write(datas)

    @api.multi
    def send_email(self):
        self.ensure_one()
        mail_pool = self.env['mail.mail']
        context = self._context.copy()
        context['base_url'] = self.env['ir.config_parameter'].get_param('web.base.url')

        template_id = self.env.ref('crm_claim_rma_custom.email_template_call_sat')

        if template_id:
            mail_id = template_id.with_context(context).send_mail(self.id)
        else:
            mail_id = 0

        if mail_id:
            mail_id_check = mail_pool.browse(mail_id)
            mail_id_check.send()
            self.email_sent = True
        else:
            raise except_orm(_('Email Error'), _('Email has not been sent'))

        return True

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
            'team_id': False,
            'opportunity_id': False,
            'duration': (duration.seconds / float(60)),
            'state': 'done',
            'brand_id': self.brand_id.id
        }
        self.write(datas)

    @api.multi
    def end_call_notif(self):
        self.end_call()
        self.send_email()
#       if self.call_type_sat == 'counsel' or self.call_type_sat == 'check_working':


class ResPartner(models.Model):
    """ Inherits partner and adds Phonecalls information in the partner form """
    _inherit = 'res.partner'

    @api.multi
    def _sat_phonecall_count(self):
        phonecall_obj = self.env['crm.phonecall']
        for partner in self:
            phonecalls = phonecall_obj.search_count([('partner_id', 'child_of', [partner.id]), ('scope', '=', 'sat')])
            partner.sat_phonecall_count = phonecalls

    sat_phonecall_count = fields.Integer(compute='_sat_phonecall_count', store=False, string='SAT Calls')
    phonecall_ids = fields.One2many('crm.phonecall', 'partner_id', 'Phonecalls', domain=[('scope', '=', 'sales')])
