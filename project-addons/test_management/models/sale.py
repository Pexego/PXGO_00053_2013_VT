# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class SaleOrder(models.Model):

    _inherit = "sale.order"

    tests = fields.Boolean(copy=False, readonly=True)

    def set_tests(self):
        for sale in self:
            sale.tests = True
        return True

    def unset_tests(self):
        for sale in self:
            sale.tests = False
        return True
