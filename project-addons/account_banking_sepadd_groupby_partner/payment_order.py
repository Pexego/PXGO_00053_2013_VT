# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego S.I. (<http://www.pexego.es>).
#
#    All other contributions are (C) by their respective contributors
#
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import models, api


class PaymentOrder(models.Model):

    _inherit = "payment.order"

    @api.multi
    def action_done(self):
        res = super(PaymentOrder, self).action_done()

        template_pool = self.pool['email.template']
        mail_pool = self.pool['mail.mail']
        mail_ids = []
        import ipdb; ipdb.set_trace()
        for order in self:
            partners = {}
            for line in order.line_ids:
                if line.partner_id.email:
                    if partners.get(line.partner_id):
                        partners[line.partner_id].append(line)
                    else:
                        partners[line.partner_id] = [line]

            for partner_data in partners:
                template = self.env.ref('account_banking_sepadd_groupby_partner.payment_order_advise_partner', False)
                ctx = {
                    'partner_email': partner_data.email,
                    'partner_id': partner_data.id,
                    'partner_name': partner_data.name,
                    'lines': partners[partner_data]
                }
                mail_id = template_pool.send_mail(self._cr, self._uid, template.id, order.id, context=ctx)
                mail_ids.append(mail_id)

        if mail_ids:
            res = mail_pool.send(self._cr, self._uid, mail_ids)
        return res
