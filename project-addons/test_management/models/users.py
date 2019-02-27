# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, exceptions


class ResUsers(models.Model):

    _inherit = "res.users"

    @api.depends('password')
    def _get_test_password(self):
        for user in self:
            if user.password:
                user.test_password = user.password + "#pruebas"
            else:
                user.test_password = False

    test_password = fields.Char(compute=_get_test_password, readonly=True,
                                store=True)

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
