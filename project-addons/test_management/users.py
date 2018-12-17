# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, fields, api, exceptions, _, SUPERUSER_ID


class ResUsers(models.Model):

    _inherit = "res.users"

    @api.one
    @api.depends('password')
    def _get_test_password(self):
        if self.password:
            self.test_password = self.password + u"#pruebas"
        else:
            self.test_password = False

    test_password = fields.Char(compute=_get_test_password, readonly=True,
                                string="Test Password", store=True)

    @api.model
    def check_credentials(self, password):
        res = self.sudo().search([('id', '=', self._uid),
                                  ('test_password', '=', password)])
        if not res:
            super(ResUsers, self).check_credentials(password)
            user = self.sudo().search([('id', '=', self._uid)])[0]
            valid_pass, replacement = user._crypt_context()\
                .verify_and_update(password, user.password_crypt)
            if valid_pass:
                is_test = self.env["res.company"].sudo().\
                    search([('test_company_id', '=', user.company_id.id)])
                if is_test:
                    user.write({'company_id': is_test[0].id})
            else:
                raise exceptions.AccessDenied()
        else:
            user = res[0]
            is_test = self.env["res.company"].sudo().\
                search([('test_company_id', '=', user.company_id.id)])
            if not is_test:
                test_company = user.company_id.test_company_id
                if not test_company:
                    raise exceptions.AccessDenied()
                else:
                    if test_company not in user.company_ids:
                        raise exceptions.AccessDenied()
                    user.write({'company_id': test_company.id})
