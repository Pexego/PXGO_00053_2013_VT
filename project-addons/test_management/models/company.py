# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResCompany(models.Model):

    _inherit = "res.company"

    test_company_id = fields.Many2one("res.company", "Tests company",
                                      context={'user_preference': False})
