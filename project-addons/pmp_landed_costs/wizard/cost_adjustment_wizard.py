from odoo import models, fields, api, _


class CostAdjustmentWizard(models.TransientModel):

    _name = "cost.adjustment.wizard"

    inserted = fields.Float('Inserted', readonly=True, digits=(10, 4))
    calculated = fields.Float('Calculated', readonly=True, digits=(10, 4))
    difference = fields.Float('Difference', readonly=True, compute='_compute_difference', digits=(10, 5))

    @api.multi
    def _compute_difference(self):
        import ipdb
        ipdb.set_trace()
        self.difference = self.inserted - self.calculated
