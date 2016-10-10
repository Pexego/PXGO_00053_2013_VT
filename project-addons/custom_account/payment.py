# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PaymentOrder(models.Model):

    _inherit = 'payment.line'

    _order = 'partner_name'

    partner_name = fields.Char(related='partner_id.name', store=True)
