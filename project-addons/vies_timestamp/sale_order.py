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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import time
from urllib import getproxies

class sale_order(osv.osv):
    """
    Ejemplos de CIFS/NIFs que sí validan:
    BE0897290877
    RO19386256
    """
    _inherit = 'sale.order'
    _columns = {
        'vies_validation_check': fields.boolean('VAT Validated through VIES?', copy=False),
        'vies_validation_timestamp': fields.datetime('Date when VAT validated through VIES', copy=False)
    }

    def check_vat_ext(self, cr, uid, ids, partner_vat, context):
        """
        """
        vat = partner_vat.replace(" ","")
        date_now = time.strftime('%Y-%m-%d %H:%M:%S')
        if vat:
            vat = vat.replace(' ','')
            try:
                from suds.client import Client
            except:
                raise osv.except_osv(_('Error'), _('import module "suds" failed - check VIES needs this module'))

            check = False
            country_code = '%s'%(vat[:2])
            vat_number = '%s'%(vat[2:])
            try:
                client = Client("http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl", proxy=getproxies())
                res = client.service.checkVat(countryCode=country_code, vatNumber=vat_number)
                result = res["valid"]
            except:
                result = False
            check = bool(res["valid"])
            if check:
                vals = {'vies_validation_check': check, 'vies_validation_timestamp': date_now}
                from reportlab.pdfgen import canvas
                sale = self.browse(cr, uid, ids)
                name = '%s.pdf' % sale.name.replace(" ","").replace("\\","").replace("/","").replace("-","_")
                c = canvas.Canvas(name)
                height= 700
                for key in dict(res):
                    c.drawString(100, height, key + u": " + tools.ustr(res[key]).replace('\n',' '))
                    height = height - 25
                c.showPage()
                c.save()
                a = open(name, "rb").read().encode("base64")
                self.write(cr, uid, ids, vals)
                attach_vals = {
                    'name': name,
                    'datas_fname': name,
                    'datas': a,
                    'res_id': sale.id,
                    'res_model': 'sale.order',
                }
                self.pool.get('ir.attachment').create(cr, uid, attach_vals)
        return True

    def action_button_confirm(self, cr, uid, ids, context=None):
        """
        Herencia del metodo de confirmar presupuesto para añadir una validación de CIF via el webservice de VIES
        """
        if context is None:
            context = {}
        for order in self.browse(cr, uid, ids, context=context):
            if order.partner_id.vat:
                self.check_vat_ext(cr, uid, ids, order.partner_id.vat, context)
        return super(sale_order,self).action_button_confirm(cr, uid, ids, context)
