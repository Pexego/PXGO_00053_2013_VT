# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Javier Colmenero Fernández$ <javier@pexego.es>
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
from openerp import api, models, fields


class stock_config_settings(models.TransientModel):
    _inherit = 'stock.config.settings'

    consult_period = \
        fields.Integer('Consult Period Stock Days',
                       help='General hystoric period for calculating '
                       'stock days of a product. It will check from today '
                       'to X period days of the last year the quantity sold. '
                       'if not sales in last year we check the period going '
                       'back since today in the current year')
    adjustement_period = \
        fields.Integer('Adjustement Period Stock Days',
                       help='General Adjustement period to calculate the '
                       'stock days of a product. It will check a period from '
                       'today back to this days, of the last and the '
                       'current year, to get the diferent trend in sales')

    @api.multi
    def get_default_consult_period(self, fields):
        domain = [('key', '=', 'configured.consult.period')]
        param_obj = self.env['ir.config_parameter'].search(domain)
        value = int(param_obj.value)
        return {'consult_period': value}

    @api.multi
    def set_consult_period(self):
        domain = [('key', '=', 'configured.consult.period')]
        param_obj = self.env['ir.config_parameter'].search(domain)
        param_obj.value = str(self.consult_period)

    @api.multi
    def get_default_adjustement_period(self, fields):
        domain = [('key', '=', 'configured.adjustement.period')]
        param_obj = self.env['ir.config_parameter'].search(domain)
        value = int(param_obj.value)
        return {'adjustement_period': value}

    @api.multi
    def set_adjustement_period(self):
        domain = [('key', '=', 'configured.adjustement.period')]
        param_obj = self.env['ir.config_parameter'].search(domain)
        param_obj.value = str(self.adjustement_period)
