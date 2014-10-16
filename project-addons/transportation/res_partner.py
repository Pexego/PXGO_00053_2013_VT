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


class res_partner(models.Model):

    _inherit = 'res.partner'
    transporter_id = fields.Many2one('transportation.transporter',
                                     'transporter')
    service_id = fields.Many2one('transportation.service',
                                 'Transport service')

    @api.onchange('country_id')
    def onchange_country_id(self):
        self.transporter_id = self.country_id.default_transporter

    @api.onchange('transporter_id')
    def onchange_transporter_id(self):
        service_ids = [x.id for x in self.transporter_id.service_ids]
        if self.service_id.id not in service_ids:
            self.service_id = False
        return {'domain': {'service_id': [('id', 'in', service_ids)]}}


class res_country(models.Model):

    _inherit = 'res.country'

    default_transporter = fields.Many2one('transportation.transporter',
                                          'Default transporter')


class res_partner_area(models.Model):

    _inherit = "res.partner.area"

    transporter_rotation_ids = fields.One2many('area.transportist.rel',
                                               'area_id', 'Rotation')

    @api.onchange('transporter_rotation_ids')
    def onchange_transporter_rotation(self):
        for rot in self.transporter_rotation_ids:
            if rot.ratio_shipping == 0:
                raise exceptions.except_orm(
                    _('Value error'), _('the ratio can not be 0'))

    @api.one
    def write(self, values):
        super(res_partner_area, self).write(values)
        for rot in self.transporter_rotation_ids:
            if rot.ratio_shipping == 0:
                raise exceptions.except_orm(
                    _('Value error'), _('the ratio can not be 0'))
