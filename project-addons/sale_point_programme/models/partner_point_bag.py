##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from odoo import models, fields
from odoo.addons.queue_job.job import job


class PartnerPointProgrammeBag(models.Model):

    _name = 'res.partner.point.programme.bag'

    name = fields.Char('Description', size=128, readonly=True)
    point_rule_id = fields.Many2one('sale.point.programme.rule', 'Rule', readonly=True)
    order_id = fields.Many2one('sale.order', 'Sale order', readonly=True)
    points = fields.Float('Points', readonly=True)
    date_order = fields.Datetime(related='order_id.date_order')
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    email_sent = fields.Boolean('Email sent', default=False)
    order_applied_id = fields.Many2one('sale.order', 'Sale order applied', readonly=True)
    applied_state = fields.Selection([
        ('no', 'No'),
        ('applied', 'Applied'),
    ], string='State', default='no')
    line_id = fields.Many2one('sale.order.line', 'Sale order line', readonly=True)

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def recalculate_partner_point_bag_accumulated(self, rule_ids, partner_id):
        bag_accumulated_obj = self.env['res.partner.point.programme.bag.accumulated']
        for rule in rule_ids:
            bag = self.env['res.partner.point.programme.bag'].search_read(
                [('point_rule_id', '=', rule.id), ('applied_state', '=', 'no'), ('partner_id', '=', partner_id.id)],
                ['points'])
            points = sum(x['points'] for x in bag)
            bag_accumulated = bag_accumulated_obj.search(
                [('partner_id', '=', partner_id.id), ('point_rule_id', '=', rule.id)])
            if bag_accumulated:
                bag_accumulated.write({'points': points})
            else:
                bag_accumulated_obj.create({'name': rule.name,
                                                      'point_rule_id': rule.id,
                                                      'points': points,
                                                      'partner_id': partner_id})
        return True


class PartnerPointProgrammeBagAccumulated(models.Model):

    _name = 'res.partner.point.programme.bag.accumulated'

    name = fields.Char('Description', size=128, readonly=True)
    point_rule_id = fields.Many2one('sale.point.programme.rule', 'Rule', readonly=True)
    points = fields.Float('Points', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)

