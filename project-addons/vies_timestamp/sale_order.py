# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    @author Alberto Luengo Cabanillas
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

from openerp import fields, models, _, tools, api, exceptions
import time
from urllib import getproxies


class SaleOrder(models.Model):
    """
    Ejemplos de CIFS/NIFs que sí validan:
    BE0897290877
    RO19386256
    """
    _inherit = 'sale.order'

    vies_validation_check = fields.Boolean('VAT Validated through VIES?',
                                           copy=False)
    vies_validation_timestamp = fields.\
        Datetime('Date when VAT validated through VIES', copy=False)
    waiting_vies_validation = fields.Boolean('Waiting for vies validation',
                                             copy=False, readonly=True)
    force_vies_validation = fields.Boolean('Vies validation forced',
                                           copy=False, readonly=True)

    @api.multi
    def check_vat_ext(self):
        """
        """
        date_now = time.strftime('%Y-%m-%d %H:%M:%S')
        result = True
        sale = self[0]
        partner_vat = sale.partner_id.vat
        url = "http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl"
        if partner_vat and not sale.force_vies_validation:
            vat = partner_vat.replace(" ", "")
            try:
                from suds.client import Client
            except:
                raise exceptions.\
                    Warning(_('import module "suds" failed - check VIES '
                              'needs this module'))

            country_code = '%s' % (vat[:2])
            vat_number = '%s' % (vat[2:])
            res = {}
            try:
                client = Client(url, proxy=getproxies())
                res = client.service.\
                    checkVat(countryCode=country_code, vatNumber=vat_number)
                result = bool(res["valid"])
            except:
                result = None

            if result is not None:
                vals = {'vies_validation_check': result,
                        'vies_validation_timestamp': date_now,
                        'waiting_vies_validation': False}
                from reportlab.pdfgen import canvas
                name = '%s_VIES.pdf' % sale.\
                    name.replace(" ", "").replace("\\", "").replace("/", "").\
                    replace("-", "_")
                c = canvas.Canvas(name)
                height = 700
                for key in dict(res):
                    c.drawString(100, height,
                                 key + u": " + tools.ustr(res[key]).
                                 replace('\n', ' '))
                    height = height - 25
                c.showPage()
                c.save()
                a = open(name, "rb").read().encode("base64")
                sale.write(vals)
                attach_vals = {
                    'name': name,
                    'datas_fname': name,
                    'datas': a,
                    'res_id': sale.id,
                    'res_model': 'sale.order',
                }
                self.env['ir.attachment'].create(attach_vals)

            if result is None or not result:
                if sale.partner_id.property_account_position and \
                        sale.partner_id.property_account_position.\
                        require_vies_validation:
                    result = False
                    sale.write({'waiting_vies_validation': True})
                else:
                    result=True
        return result

    @api.multi
    def action_force_vies_validation(self):
        self.write({'force_vies_validation': True,
                    'waiting_vies_validation': False})
        for order in self:
            followers = order.message_follower_ids
            order.message_post(body=_("The user %s forced vies validation.") %
                               self.env.user.name,
                               subtype='mt_comment',
                               partner_ids=followers)
        return True

    @api.multi
    def action_risk_approval(self):
        self.check_vat_ext()
        return super(SaleOrder, self).action_risk_approval()
