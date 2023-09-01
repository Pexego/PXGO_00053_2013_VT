from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_national_supplier = fields.Boolean(
        'Is national supplier',
        compute='_compute_is_national_supplier',
        store=True
    )

    @api.depends('supplier', 'property_account_position_id')
    def _compute_is_national_supplier(self):
        """
        Calculates if a supplier has intra or national fiscal position
        """
        national_fiscal_position_id = self.env.ref('l10n_es.1_fp_nacional').id
        intra_fiscal_position_id = self.env.ref('l10n_es.1_fp_intra').id
        for partner in self:
            partner.is_national_supplier = partner.supplier and partner.property_account_position_id.id in (
                national_fiscal_position_id,
                intra_fiscal_position_id
            )
