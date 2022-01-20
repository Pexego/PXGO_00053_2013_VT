from odoo import models, fields, api
from odoo.addons.queue_job.job import job


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @job()
    def cancel_draft_moves(self):
        move_lines = self.env['stock.move'].search([('origin', 'like', self.name + '%'), ('picking_id', '=', False)])
        move_lines._action_cancel()
