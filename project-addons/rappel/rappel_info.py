# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
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


class RappelCurrentInfo(models.Model):

    _name = "rappel.current.info"

    CALC_MODE = [('fixed', 'Fixed'), ('variable', 'Variable')]
    QTY_TYPE = [('quantity', 'Quantity'), ('value', 'Value')]
    CALC_AMOUNT = [('percent', 'Percent'), ('qty', 'Quantity')]

    rappel_id = fields.Many2one("rappel", "Rappel", required=True)
    partner_id = fields.Many2one("res.partner", "Customer", required=True)
    date_start = fields.Date("Start date", required=True)
    date_end = fields.Date("End date", required=True)
    amount = fields.Float("Current Amount", required=True)
    qty_type = fields.Selection(QTY_TYPE, 'Quantity type', readonly=True,
                                related="rappel_id.qty_type")
    calc_mode = fields.Selection(CALC_MODE, 'Fixed/Variable', readonly=True,
                                 related="rappel_id.calc_mode")
    calc_amount = fields.Selection(CALC_AMOUNT, 'Percent/Quantity',
                                   readonly=True,
                                   related="rappel_id.calc_amount")
    curr_qty = fields.Float("Curr. qty", readonly=True)
    section_id = fields.Many2one("rappel.section", "Section")
    section_goal = fields.Float("Section goal", readonly=True,
                                related="section_id.rappel_until")
