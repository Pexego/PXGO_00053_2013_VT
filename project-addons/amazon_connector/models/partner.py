from odoo import models, fields, api, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    amazon_child_ids = fields.One2many('res.partner', 'amazon_parent_id', string='Amazon Contacts')
    amazon_parent_id = fields.Many2one('res.partner')
    retail_phone = fields.Char("Retail Phone")

    @api.onchange('retail_phone', 'country_id', 'company_id')
    def _onchange_retail_phone_validation(self):
        if self.retail_phone:
            self.retail_phone = self.phone_format(self.retail_phone)

    @api.depends('amazon_parent_id.name')
    def _compute_display_name(self):
        super(ResPartner, self)._compute_display_name()
        for partner in self:
            if partner.amazon_parent_id:
                partner.display_name = "%s, %s" % (partner.amazon_parent_id.name, partner.display_name)

