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
from openerp.exceptions import except_orm
from datetime import datetime

class partner_visit(models.Model):
    """ Model for Partner Visits """
    _name = "partner.visit"
    _rec_name = "partner_id"
    _description = "Partner Visit"
    _order = "visit_date desc"

    create_date = fields.Datetime('Creation Date', readonly=True, default=fields.Datetime.now)
    visit_date = fields.Datetime('Visit Date', required=True)
    user_id = fields.Many2one('res.users', 'External salesperson', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    partner_address = fields.Char('Address', readonly=True, compute='get_address')
    description = fields.Text('Summary', required=True)
    visit_state = fields.Selection([('log', 'Log'), ('schedule', 'Schedule')], string='Status', readonly=True)
    email_sent = fields.Boolean('Email sent', default=False, readonly=True)
    salesperson_select = fields.Many2one('res.users', 'Salesperson to notify')
    confirm_done = fields.Boolean('Done', default=False)

    _defaults = {
        'create_date': fields.Datetime.now(),
        'user_id': lambda self, cr, uid, ctx: uid,
        'salesperson_select': False
    }

    @api.multi
    def validate_fields(self, self_data, changes):
        date_now = str(datetime.now())
        res = {}

        if 'visit_date' in changes:
            visit_date = changes['visit_date']
            if visit_date:
                difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                             datetime.strptime(visit_date, '%Y-%m-%d %H:%M:%S')
                difference = difference.total_seconds() / float(60)
                if self_data.visit_state == 'log' and difference < 0:
                    raise except_orm(_('Invalid date'), _('Date must be lower than current date in a logged visit'))
                elif self_data.visit_state == 'schedule' and difference > 0:
                    raise except_orm(_('Invalid date'), _('Date must be bigger than current date in a scheduled visit'))
            if 'confirm_done' in changes:
                confirm_done = changes['confirm_done']
                if confirm_done and difference < 0:
                    raise except_orm(_('Invalid Action'), _('You cannot confirm the visit because schedule date '
                                                            'is after current date'))
        else:
            if 'confirm_done' in changes:
                confirm_done = changes['confirm_done']
                # Case when visit_date has not been changed -> recalculate the difference with "self.visit_date"
                difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                    datetime.strptime(self_data.visit_date, '%Y-%m-%d %H:%M:%S')
                difference = difference.total_seconds() / float(60)
                if confirm_done and difference < 0:
                    raise except_orm(_('Invalid Action'), _('You cannot confirm the visit because schedule date '
                                                            'is after current date'))
                elif confirm_done and difference > 0:
                    res['visit_state'] = 'log'
        return res

    @api.model
    def create(self, vals):
        res = super(partner_visit, self).create(vals)
        res_change = self.validate_fields(res, vals)
        return res

    @api.multi
    def write(self, datas):
        res = super(partner_visit, self).write(datas)
        res_change = self.validate_fields(self, datas)
        if 'visit_state' in res_change:
            self.visit_state = res_change['visit_state']
        return res

    @api.one
    def get_address(self):
        if self.partner_id:
            address_array = [self.partner_id.street, self.partner_id.city, self.partner_id.country_id.name]
            self.partner_address = u", ".join([x for x in address_array if x])

    @api.one
    def send_email(self):
        ir_model_data = self.env['ir.model.data']

        context = self._context.copy()
        context['base_url'] = self.env['ir.config_parameter'].get_param('web.base.url')

        if self.visit_state == 'log':
            template_id = ir_model_data.get_object_reference(
                'external_salesperson_visit', 'email_template_logged_visits')[1]
        elif self.visit_state == 'schedule':
            template_id = ir_model_data.get_object_reference(
                'external_salesperson_visit', 'email_template_scheduled_visits')[1]
        else:
            template_id = 0

        if template_id:
            mail_id = self.pool.get('email.template').send_mail(self._cr, self._uid,
                                                                template_id, self.id, force_send=True, context=context)
        else:
            mail_id = 0

        if mail_id:
            self.email_sent = True
        else:
            raise except_orm(_('Email Error'), _('Email has not been sent'))

        return True

