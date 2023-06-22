
from odoo import models, fields, api, exceptions, _


class ProductIncidence(models.Model):
    _name = 'product.incidence'

    name = fields.Char(required=True)

    description = fields.Text()

    warn = fields.Boolean()

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    incidence_ids = fields.One2many(
        comodel_name='product.incidence',
        inverse_name='product_id',
        string='Incidences',
        required=False)

    @api.multi
    def _get_incidences_warn_description(self):

        import wdb
        wdb.set_trace()

        description = ""
        for product in self:
            incidences = product.incidence_ids.filtered(lambda i: i.warn)
            if incidences:
                description_product = "%s:\n" % product.default_code
                for incidence in incidences:
                    description_product += "- %s: %s\n" % (incidence.name, incidence.description or "")
                description += description_product
        return description
