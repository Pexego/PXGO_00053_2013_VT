# -*- coding: utf-8 -*-
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

from openerp import models, fields


class PartnerPointProgrammeBag(models.Model):

    _name = "res.partner.point.programme.bag"

    name = fields.Char('Description', size=128, readonly=True)
    point_rule_id = fields.Many2one('sale.point.programme.rule', 'Rule',
                                    readonly=True)
    order_id = fields.Many2one('sale.order', 'Sale order', readonly=True)
    points = fields.Integer('Points', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
