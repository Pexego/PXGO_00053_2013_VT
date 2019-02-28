# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class Partner(models.Model):

    _inherit = "res.partner"

    @api.multi
    def _pending_orders_amount(self):
        web_user = self.env['ir.config_parameter'].get_param('web.user.buyer')
        if self.env.user.email != web_user:
            for partner in self:
                total = 0.0
                sale_lines = self.env['sale.order.line'].\
                    search([('order_id.partner_id', 'child_of', [partner.id]),
                            ('state', '=', 'sale'),
                            ('qty_to_invoice', '>', 0.0)])

                for line in sale_lines:
                    total += line.qty_to_invoice * \
                        (line.price_unit * (1 - (line.discount or 0.0) /
                         100.0))

                partner.pending_orders_amount = total

    email2 = fields.Char('Second Email')
    not_send_following_email = fields.Boolean()
    unreconciled_purchase_aml_ids = fields.\
        One2many('account.move.line', 'partner_id',
                 domain=[('full_reconcile_id', '=', False),
                         ('account_id.internal_type', '=', 'payable'),
                         ('account_id.not_payment_followup', '=', False),
                         ('move_id.state', '!=', 'draft')])
    attach_picking = fields.Boolean("Attach picking")
    newsletter = fields.Boolean('Newsletter')
    pending_orders_amount = fields.Float(compute="_pending_orders_amount",
                                         string='Uninvoiced Orders')

    @api.onchange("user_id")
    def on_change_user_id(self):
        self.payment_responsible_id = self.user_id.id
        if self.user_id and self.user_id.sale_team_id:
            self.team_id = self.user_id.sale_team_id.id
