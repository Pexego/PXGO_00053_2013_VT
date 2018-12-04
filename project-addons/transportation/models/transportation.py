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

from odoo import models, fields


class Transporter(models.Model):

    _name = 'transportation.transporter'

    name = fields.Char('Name', size=64, required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    service_ids = fields.Many2many('transportation.service',
                                   'transporter_service_rel',
                                   'transporter_id',
                                   'service_id',
                                   'Services')


class TransportService(models.Model):

    _name = 'transportation.service'

    name = fields.Char('Name', size=64, required=True)
    transporter_ids = fields.Many2many('transportation.transporter',
                                       'transporter_service_rel',
                                       'service_id',
                                       'transporter_id',
                                       'Transporters')
