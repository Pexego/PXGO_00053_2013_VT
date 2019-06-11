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


class SalePointProgrammeRule(models.Model):

    _name = 'sale.point.programme.rule'

    name = fields.Char('Description', required=True, size=128)
    date_start = fields.Date('Start date')
    date_end = fields.Date('End date')
    points = fields.Integer('Points / Participations', required=True)
    modality = fields.Selection([('point', 'points'), ('participation', 'participations')], 'Modality', default='point',required=True)
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

    @api.multi
    @api.constrains('date_start', 'date_end')
    def validate(self):
        for rule in self:
            if rule.date_end < rule.date_start:
                raise exceptions.Warning(_("End date is less than start date"))

    @api.multi
    def evaluate(self, amount):
        for rule in self:
            if rule.operator == "for_each":
                mult = amount / (rule.value or 1.0)
                return int(mult * rule.points)
            else:
                if eval(str(amount) + rule.operator + str(rule.value)):
                    return rule.points
                else:
                    return 0


