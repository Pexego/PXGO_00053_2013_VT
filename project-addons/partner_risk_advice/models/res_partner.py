# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    risk_advice_ids = fields.One2many("partner.risk.advice", "partner_id")
    rma_warn = fields.Selection(
        [('no-message', 'No Message'), ('warning', 'Warning'),
         ('block', 'Blocking Message')],
        'Invoice', help='Selecting the "Warning" option will notify user with \
the message, Selecting "Blocking Message" will throw an exception with the \
message and block the flow. The Message has to be written in the next field.',
        required=True, default='no-message')
    rma_warn_msg = fields.Text('Message for RMA')
