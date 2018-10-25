# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ProductVersion(models.Model):

    _name = "product.version"

    name = fields.Text("Description", required=True)
    version = fields.Char("Version", required=True, size=64)
    product_tmpl_id = fields.Many2one("product.template", "Product",
                                      required=True)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    version_ids = fields.One2many("product.version", "product_tmpl_id",
                                  "Versions")
