# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
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

from openerp import fields, models, api
from datetime import datetime, time

class product_category(models.Model):

    _inherit='product.category'

    devaluation_journal_id = fields.Many2one('account.journal', 'Journal',
                                             default=lambda self:
                                             self.env.user.company_id.devaluation_journal_id)
    devaluation_account_provision_id = fields.Many2one('account.account', 'Provision Account',
                                                       domain=[('type', '<>', 'view'), ('type', '<>', 'closed')],
                                                       default=lambda self:
                                                       self.env.user.company_id.devaluation_account_provision_id)
    devaluation_account_debit_id = fields.Many2one('account.account', 'Debit Account',
                                                   domain=[('type', '<>', 'view'), ('type', '<>', 'closed')],
                                                   default=lambda self:
                                                   self.env.user.company_id.devaluation_account_debit_id)
    devaluation_account_credit_id = fields.Many2one('account.account', 'Credit Account',
                                                    domain=[('type', '<>', 'view'), ('type', '<>', 'closed')],
                                                    default=lambda self:
                                                    self.env.user.company_id.devaluation_account_credit_id)

class product_devaluation(models.Model):

    _name = "product.devaluation"

    @api.one
    def _get_total_dev(self):
        self.total_dev=self.quantity*(self.price_after-self.price_before)

    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')
    price_before = fields.Float('Price Before')
    price_after = fields.Float ('Price After')
    total_dev = fields.Float ("Total Devaluation", compute = _get_total_dev)
    date_dev = fields.Date('Devaluated on', default = fields.datetime.now())
    #TODO: Migrar
    #period_id = fields.Many2one('account.period', 'Period', default=lambda self:
    #    self.env['account.period'].find(time())[0], required=True)
    accounted_ok = fields.Boolean("Accounted", default=False)


