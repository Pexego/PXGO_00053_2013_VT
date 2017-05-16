# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp import models, fields, api, exceptions, _
from openerp.osv import fields as fields2
from openerp.exceptions import except_orm, ValidationError
from datetime import datetime


class partner_visit(models.Model):
    """ Model for Partner Visits """
    _name = "partner.visit"
    _rec_name = "partner_id"
    _description = "Partner Visit"
    _order = "visit_date desc"
    _inherit = ['mail.thread']

    create_date = fields.Datetime('Creation Date', readonly=True, default=fields.Datetime.now)
    visit_date = fields.Datetime('Visit Date', required=True)
    user_id = fields.Many2one('res.users', 'External salesperson', readonly=True, default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    partner_address = fields.Char('Address', readonly=True, compute='get_address')
    description = fields.Text('Summary', required=True)
    visit_state = fields.Selection([('log', 'Log'), ('schedule', 'Schedule')], string='Status', readonly=True)
    email_sent = fields.Boolean('Email sent', default=False, readonly=True)
    salesperson_select = fields.Many2one('res.users', 'Notify to', readonly=True,
                                         compute='get_internal_salesperson', store=True)
    confirm_done = fields.Boolean('Done', default=False)

    @api.one
    @api.constrains('confirm_done')
    def validate_confirm_done(self):
        date_now = str(datetime.now())

        difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                     datetime.strptime(self.visit_date, '%Y-%m-%d %H:%M:%S')
        difference = difference.total_seconds() / float(60)

        if self.confirm_done:
            if difference < 0:
                raise ValidationError("You cannot confirm the visit because schedule date is after current date")

        return True

    @api.one
    @api.constrains('visit_date')
    def validate_visit_date(self):
        date_now = str(datetime.now())

        if self.visit_date:
            difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                         datetime.strptime(self.visit_date, '%Y-%m-%d %H:%M:%S')
            difference = difference.total_seconds() / float(60)
            if self.visit_state == 'log' and difference < 0:
                raise ValidationError("Date must be lower than current date in a logged visit")
            elif self.visit_state == 'schedule' and difference > 0:
                raise ValidationError("Date must be bigger than current date in a scheduled visit")
        return True

    @api.one
    def write(self, datas):
        if 'confirm_done' in datas and datas['confirm_done']:
                datas['visit_state'] = 'log'
        res = super(partner_visit, self).write(datas)
        return res

    @api.one
    def get_address(self):
        if self.partner_id:
            address_array = [self.partner_id.street, self.partner_id.city, self.partner_id.country_id.name]
            self.partner_address = u", ".join([x for x in address_array if x])

    @api.one
    @api.depends('partner_id')
    def get_internal_salesperson(self):
        if self.partner_id:
            self.salesperson_select = self.partner_id.commercial_partner_id.user_id.id

    @api.one
    def send_email(self):
        mail_pool = self.env['mail.mail']
        context = self._context.copy()
        context['base_url'] = self.env['ir.config_parameter'].get_param('web.base.url')

        if self.visit_state == 'log':
            template_id = self.env.ref(
                'external_salesperson_visit.email_template_logged_visits', False)
        elif self.visit_state == 'schedule':
            template_id = self.env.ref(
                'external_salesperson_visit.email_template_scheduled_visits', False)
        else:
            template_id = 0

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


class res_partner(models.Model):
    """ Inherits partner and adds Visit information in the partner form """
    _inherit = 'res.partner'

    def _visits_count(self, cr, uid, ids, field_name, arg, context=None):
        visits = self.pool['partner.visit']
        res = {}
        for partner in self.browse(cr, uid, ids):
            visit_ids = visits.search(cr, uid, [('partner_id', '=', partner.id), ('visit_state', '=', 'log')])
            res[partner.id] = len(visit_ids)
        return res

    _columns = {
        'visit_count': fields2.function(_visits_count, string="Visits", type="integer"),
    }

