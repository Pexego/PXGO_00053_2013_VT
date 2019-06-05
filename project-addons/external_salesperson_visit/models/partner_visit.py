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
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime


class PartnerVisit(models.Model):
    """ Model for Partner Visits """
    _name = 'partner.visit'
    _rec_name = 'partner_id'
    _description = "Partner Visit"
    _order = 'visit_date desc'
    _inherit = ['mail.thread']

    create_date = fields.Datetime("Creation Date", readonly=True, default=fields.Datetime.now)
    visit_date = fields.Datetime("Visit Date", required=True)
    user_id = fields.Many2one('res.users', "External salesperson", readonly=True, default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner', "Partner", required=True)
    partner_ref = fields.Char("Ref. Contact", readonly=True, compute='get_partner_ref')
    partner_address = fields.Char("Address", readonly=True, compute='get_address')
    description = fields.Text("Summary", required=True)
    visit_state = fields.Selection([('log', "Log"), ('schedule', "Schedule")], string="Status", readonly=True)
    email_sent = fields.Boolean("Email sent", default=False, readonly=True)
    salesperson_select = fields.Many2one('res.users', "Notify to", readonly=True,
                                         compute='get_internal_salesperson', store=True)
    add_user_email = fields.Many2one('res.users', "CC to")
    confirm_done = fields.Boolean("Done", default=False)

    partner_pricelist = fields.Many2one(related='partner_id.property_product_pricelist', readonly=True)
    partner_annual_invoiced = fields.Float(related='partner_id.annual_invoiced', readonly=True)
    partner_past_year_invoiced = fields.Float(related='partner_id.past_year_invoiced', readonly=True)
    partner_monthly_invoiced = fields.Float(related='partner_id.monthly_invoiced', readonly=True)
    partner_past_month_invoiced = fields.Float(related='partner_id.past_month_invoiced', readonly=True)

    area_id = fields.Many2one('res.partner.area', 'Area', readonly=True)
    region_ids = fields.Many2many(related='area_id.commercial_region_ids')
    partner_visit_count = fields.Integer(string='Visits', related='partner_id.visit_count', readonly=True)
    partner_visit_current_year = fields.Integer(string='Current year visits', readonly=True, compute='get_visit_current_year')

    @api.one
    @api.constrains('confirm_done')
    def validate_confirm_done(self):
        date_now = str(datetime.now())

        difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                     datetime.strptime(self.visit_date, '%Y-%m-%d %H:%M:%S')
        difference = difference.total_seconds()

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

    @api.multi
    def write(self, data):
        if 'confirm_done' in data and data['confirm_done']:
                data['visit_state'] = 'log'
        res = super(PartnerVisit, self).write(data)
        return res

    @api.one
    def get_partner_ref(self):
        if self.partner_id:
            self.partner_ref = self.partner_id.ref

    @api.one
    def get_address(self):
        if self.partner_id:
            address_array = [self.partner_id.street, self.partner_id.city, self.partner_id.country_id.name]
            self.partner_address = u", ".join([x for x in address_array if x])

    @api.one
    @api.depends('partner_id')
    def get_internal_salesperson(self):
        if self.partner_id:
            self.salesperson_select = self.partner_id.sudo().commercial_partner_id.user_id.id

    @api.multi
    @api.onchange('add_user_email')
    def onchange_user_cc(self):
        if self.add_user_email:
            res = {'warning': {
                'title': _('Warning'),
                'message': _('CC user has been changed. Remember that it is necessary to click on "Notify by email" '
                             'button to send email')
            }}
            return res

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id.area_id:
            self.area_id = self.partner_id.area_id.id
        else:
            self.area_id = self.partner_id.sudo().commercial_partner_id.area_id.id

    @api.one
    def send_email(self):
        mail_pool = self.env['mail.mail']
        context = self._context.copy()
        context['base_url'] = self.env['ir.config_parameter'].get_param('web.base.url')

        if self.visit_state == 'log':
            template_id = self.env.ref('external_salesperson_visit.email_template_logged_visits', False)
        elif self.visit_state == 'schedule':
            template_id = self.env.ref('external_salesperson_visit.email_template_scheduled_visits', False)
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

    @api.multi
    def get_visit_current_year(self):

        for visit in self:
            date_now = datetime.now()
            start_year = str(date_now.year) + '-01-01'
            visit_ids = self.search_count([('partner_id', 'child_of', [visit.partner_id.id]), ('visit_state', '=', 'log'), ('visit_date', '>=', [start_year])])
            visit.partner_visit_current_year = visit_ids

class ResPartner(models.Model):
    """ Inherits partner and adds Visit information in the partner form """
    _inherit = 'res.partner'

    @api.multi
    def _visits_count(self):
        visits = self.env['partner.visit']
        for partner in self:
            visit_ids = visits.search_read([('partner_id', 'child_of', [partner.id]),
                                            ('visit_state', '=', 'log')], ['id'])
            partner.visit_count = len(visit_ids)

    visit_count = fields.Integer(string="Visits", compute='_visits_count')

