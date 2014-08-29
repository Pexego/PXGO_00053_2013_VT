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


class area_transportist_rel(models.Model):

    _name = "area.transportist.rel"

    area_id = fields.Many2one('res.partner.area', 'Area')

    transporter_id = fields.Many2one('transportation.transporter',
                                     'Transporter')

    percentage_shipping = fields.Float('Percentage')


class transport_assigned(models.Model):

    _name = "transport.assigned"

    date = fields.Date('Date')
    area_id = fields.Many2one('res.partner.area', 'Area')
    transporter_id = fields.Many2one('transportation.transporter', 'Transporter')
    sale_id = fields.Many2one('sale.order', 'Sale')

    @api.returns('transportation.transporter')
    def get_transporter(self, partner):
        """
            Not need to be called from recordset
            Returns the transporter recomended for this area.
        """
        all_assignments = self.search([('area_id', '=', partner.area_id.id),
                                       ('date', '=', fields.Date.today())])

        return self.env['transportation.transporter'].search([])[0]



