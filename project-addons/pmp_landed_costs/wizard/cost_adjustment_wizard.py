from odoo import models, fields, api, _


class CostAdjustmentWizard(models.TransientModel):

    _name = "cost.adjustment.wizard"

    inserted = fields.Float('Inserted', readonly=True)
    calculated = fields.Float('Calculated', readonly=True)
    difference = fields.Float('Difference', readonly=True)
