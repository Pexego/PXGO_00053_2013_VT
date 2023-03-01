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

from odoo import models, fields, api, _, exceptions
from datetime import datetime


class SalePointProgrammeRule(models.Model):
    _name = 'sale.point.programme.rule'

    name = fields.Char('Description', required=True, size=128)
    date_start = fields.Date('Start date')
    date_end = fields.Date('End date')
    points = fields.Float('Points / Participations', required=True)
    modality = fields.Selection([('point', 'points'), ('participation', 'participations')], 'Modality', default='point',
                                required=True)
    category_id = fields.Many2one('product.category', 'Category')
    product_id = fields.Many2one('product.product', 'Product')
    product_brand_id = fields.Many2one('product.brand', 'Brand')
    attribute = fields.Selection([('amount_untaxed', 'Amount untaxed'),
                                  ('product_qty', 'Product qty.')],
                                 'Attribute to value', required=True,
                                 default='amount_untaxed')
    operator = fields.Selection([('for_each', 'For each'),
                                 ('>', 'Greater than'),
                                 ('<', 'Less than'),
                                 ('==', 'Equal')],
                                'Operator', required=True, default='for_each')
    value = fields.Float('Value', digits=(16, 2), required=True, default=1.0)
    active = fields.Boolean('Active', default=True)
    integer_points = fields.Boolean(default=True)
    partner_category_id = fields.Many2one('res.partner.category', string='Tags')

    @api.multi
    @api.constrains('date_start', 'date_end')
    def validate(self):
        for rule in self:
            if rule.date_end and rule.date_start and rule.date_end < rule.date_start:
                raise exceptions.Warning(_("End date is less than start date"))

    @api.multi
    def evaluate(self, amount):
        for rule in self:
            if rule.operator == "for_each":
                points = (amount / (rule.value or 1.0)) * rule.points
            else:
                points = rule.points if eval(str(amount) + rule.operator + str(rule.value)) else 0
            if rule.integer_points:
                return int(points)
            return points

    def evaluate_rule_dict(self, record, dicc):
        if record.id not in dicc:
            return False
        record = dicc[record.id]
        return self.evaluate(record.get('qty',0)) if self.attribute == 'product_qty' else self.evaluate(record.get('amount',0))

    @api.model
    def compute_partner_point_bag_accumulated(self):
        now = datetime.now()
        bag_accumulated_obj = self.env['res.partner.point.programme.bag.accumulated']
        rules = self.env['sale.point.programme.rule'].search(['|', ('date_start', '<=', now),
                                                              ('date_start', '=', False),
                                                              '|', ('date_end', '>=', now),
                                                              ('date_end', '=', False)])
        bags_updated = self.env['res.partner.point.programme.bag.accumulated']
        bags = self.env['res.partner.point.programme.bag'].read_group(
            [('point_rule_id', 'in', rules.ids), ('applied_state', '=', 'no')],
            ['point_rule_id', 'points', 'partner_id'], ['point_rule_id', 'partner_id'], lazy=False)
        mapped_data = {data['partner_id'][0]:
                           {'points': data['points'], 'point_rule_id': data['point_rule_id']} for data in bags}
        for partner_id in mapped_data:
            points = mapped_data[partner_id]['points']
            rule_id = mapped_data[partner_id]['point_rule_id']
            bag_accumulated = bag_accumulated_obj.search(
                [('partner_id', '=', partner_id), ('point_rule_id', '=', rule_id[0])])
            if bag_accumulated:
                bag_accumulated.write({'points': points})
            else:
                bag_accumulated = bag_accumulated_obj.create({'name': rule_id[1],
                                                      'point_rule_id': rule_id[0],
                                                      'points': points,
                                                      'partner_id': partner_id})
            bags_updated |= bag_accumulated
        if not rules:
            return
        domain = [('point_rule_id', 'in', rules.ids)]
        if bags_updated:
            domain += [('id', 'not in', bags_updated.ids)]
        bags_to_unlink = self.env['res.partner.point.programme.bag.accumulated'].search(domain)
        if bags_to_unlink:
            bags_to_unlink.unlink()
