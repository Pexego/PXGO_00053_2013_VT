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


class ClaimLine(models.Model):

    _inherit = "claim.line"

    @api.onchange('prodlot_id')
    def onchange_prodlot_id(self):
        products = self.env['sim.type'].search([]).mapped('product_id')
        if self.product_id in products:
            sims = self.prodlot_id.upper().replace(" ", "").split(',')
            sim_packages = self.env['sim.package'].search([('code', 'in', sims)])
            if not sim_packages or len(sim_packages) != len(sims) or len(sim_packages) != self.product_returned_quantity:
                raise UserError(_("You have introduced something wrong. Check the format"))
            else:
                sim_packages_p = self.env['sim.package'].search([('code', 'in', sims), ('partner_id', '=', self.claim_id.partner_id.id)])
                if not sim_packages_p or len(sim_packages_p) != len(sims) or len(sim_packages_p) != self.product_returned_quantity:
                    raise UserError(_("Some introduced SIMs are not assigned to %s") % self.claim_id.partner_id.name)
