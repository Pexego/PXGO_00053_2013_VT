# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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

from openerp import models, fields, api, exceptions, _
import math


class area_transportist_rel(models.Model):

    _name = "area.transportist.rel"

    area_id = fields.Many2one('res.partner.area', 'Area')

    transporter_id = fields.Many2one('transportation.transporter',
                                     'Transporter')

    ratio_shipping = fields.Float('ratio')


class transportation_daily(models.Model):

    _name = "transportation.daily"

    date = fields.Date('Date')
    area_id = fields.Many2one('res.partner.area', 'Area')
    assignations = fields.One2many('assignation.counter', 'daily_assigned', 'Assignations')

    def create(self, vals):
        counter_obj =  self.env['assignation.counter']
        obj = super(transportation_daily, self).create(vals)
        for transporter in obj.area_id.transporter_rotation_ids:
            counter_vals = {
                'transporter': transporter.transporter_id.id,
                'ratio': transporter.ratio_shipping,
                'daily_assigned': obj.id,
            }
            counter_obj.create(counter_vals)
        return obj

    @api.returns('transportation.transporter')
    def get_transporter(self, partner):
        """
            Returns the transporter recomended for this area.
        """
        counter_obj =  self.env['assignation.counter']

        if partner.transporter_id:
            return partner.transporter_id
        if self.assignations:
            return self.assignations[0].transporter

    @api.one
    def assign_transporter(self, transporter):
        # se aumenta el contador del nuevo partner
        counter = self.env['assignation.counter'].search(
            [('daily_assigned', '=', self.id),
             ('transporter', '=', transporter.id)])
        if counter:
            counter[0].quantity += 1

class assignation_counter(models.Model):

    _name = 'assignation.counter'
    _order = 'rot_counter, ratio desc'

    daily_assigned = fields.Many2one('transportation.daily', 'daily')
    transporter = fields.Many2one('transportation.transporter', 'Transporter')
    quantity = fields.Float('Quantity', default=0)
    ratio = fields.Integer('Ratio')
    rot_counter = fields.Integer('Rotation counter', compute='_get_rot_counter', store=True)

    @api.one
    @api.depends('quantity', 'ratio')
    def _get_rot_counter(self):
        if self.ratio:
            self.rot_counter = int(math.floor(self.quantity / self.ratio))
        else:
            self.rot_counter = 0


