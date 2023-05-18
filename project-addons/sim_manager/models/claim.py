from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ClaimMakePicking(models.TransientModel):

    _inherit = "claim_make_picking.wizard"

    @api.multi
    def create_move(self, wizard_line, p_type, picking_id, claim, note):
        super().create_move(wizard_line, p_type, picking_id, claim, note)
        claim_line = wizard_line.claim_line_id
        claim_line_id = claim_line.id
        move = picking_id.move_lines.filtered(lambda l: l.claim_line_id.id == claim_line_id)
        move.write({'lots_text': claim_line.prodlot_id})


class ClaimMakePickingFromPicking(models.TransientModel):

    _inherit = 'claim_make_picking_from_picking.wizard'

    @api.multi
    def action_create_picking_from_picking(self):
        for pick_line in self.picking_line_ids:
            move = pick_line.move_id
            if move.product_id.track_serial and not move.claim_line_id.prodlot_id:
                raise UserError(_("You must specify the serial number of the serial products"))
            elif move.claim_line_id.product_id.track_serial and move.claim_line_id.prodlot_id:
                move.lots_text = move.claim_line_id.prodlot_id
        res = super(ClaimMakePickingFromPicking, self).action_create_picking_from_picking()
        return res


class ClaimLine(models.Model):

    _inherit = "claim.line"

    @api.onchange('prodlot_id')
    def onchange_prodlot_id(self):
        super().onchange_prodlot_id()
        if self.product_id:
            products = self.env['sim.type'].search([('product_id', '=', self.product_id.id)])
            if products:
                sims = self.prodlot_id.upper().replace(" ", "").split(',')
                sim_packages = self.env['sim.package'].search([('code', 'in', sims)])
                if not sim_packages or len(sim_packages) != len(sims) or len(sim_packages) != self.product_returned_quantity:
                    raise UserError(_("The serial numbers cannot be found in the system. Check the serials and the format."))
                else:
                    sim_packages_p = self.env['sim.package'].search([('code', 'in', sims), ('partner_id', '=', self.claim_id.partner_id.id)])
                    if not sim_packages_p or len(sim_packages_p) != len(sims) or len(sim_packages_p) != self.product_returned_quantity:
                        raise UserError(_("Some introduced SIMs are not assigned to %s") % self.claim_id.partner_id.name)
