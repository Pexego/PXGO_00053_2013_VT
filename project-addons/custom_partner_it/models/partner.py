##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pcomunitea.com>$
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

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import Warning
#TODO: (Ahora es account_credit_control) from openerp.addons.account_followup.report import account_followup_print
from collections import defaultdict
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import dateutil.relativedelta,re
from calendar import monthrange
from odoo.addons.phone_validation.tools import phone_validation

class ResPartner(models.Model):
    _inherit = 'res.partner'

    codice_destinatario = fields.Char(
        "Addressee Code",
        help="The code, 7 characters long, assigned by ES to subjects with an "
             "accredited channel; if the addressee didn't accredit a channel "
             "to ES and invoices are received by PEC, the field must be "
             "filled with zeros ('0000000').",
        default='0000000', required=True, readonly=True)

    pec_destinatario = fields.Char(
        "Addressee PEC",
        help="PEC to which the electronic invoice will be sent. "
             "Must be filled "
             "ONLY when the information element "
             "<CodiceDestinatario> is '0000000'",required=False
    )

    electronic_invoice_subjected = fields.Boolean(
        "Subjected to Electronic Invoice", readonly=True,default=True)





