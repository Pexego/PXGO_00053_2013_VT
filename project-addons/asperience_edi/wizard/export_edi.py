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

from openerp import models, api, exceptions, _


class ExportEdiWzd(models.TransientModel):

    _name = "export.edi.wzd"

    @api.multi
    def export(self):
        if self.env.context['active_model'] == "account.invoice":
            for invoice in self.env["account.invoice"].\
                    browse(self.env.context['active_ids']):
                if invoice.state in ('cancel', 'draft', 'proforma'):
                    raise exceptions.Warning(_('Invoice must be opened or '
                                               'done'))
            invoic = self.env.ref('asperience_edi.edi_invoic')
            invoic.export_csv()
        return True
