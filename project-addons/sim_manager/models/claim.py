from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ClaimMakePicking(models.TransientModel):

    _inherit = "claim_make_picking.wizard"

    @api.multi
    def create_move(self, claim_line, p_type, picking_id, claim, note, write_field):
        super().create_move(claim_line, p_type, picking_id, claim, note, write_field)
        claim_line_id = claim_line.id
        move = picking_id.move_lines.filtered(lambda l: l.claim_line_id.id == claim_line_id)
        move.write({'lots_text': claim_line.prodlot_id})

    @api.multi
    def action_create_picking(self):
        for wizard_claim_line in self.claim_line_ids:
            if wizard_claim_line.product_id.track_serial and not wizard_claim_line.prodlot_id:
                raise UserError(_("You must specify the serial number of the serial products"))
        res = super(ClaimMakePicking, self).action_create_picking()
        return res
