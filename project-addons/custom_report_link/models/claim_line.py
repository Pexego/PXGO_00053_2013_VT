from odoo import models, fields


class ClaimLine(models.Model):

    _inherit = 'claim.line'

    printable_test = fields.Boolean("Printable", default=True)

    claim_origine = fields.Selection([('broken_down', 'Broken down product'),
                                      ('not_appropiate', 'Not appropiate product'),
                                      ('cancellation', 'Order cancellation'),
                                      ('damaged', 'Damaged delivered product'),
                                      ('error', 'Shipping error'),
                                      ('exchange', 'Exchange request'),
                                      ('lost', 'Lost during transport'),
                                      ('other', 'Other')
                                      ],
                                     'Claim Subject',
                                     required=True,
                                     help="To describe the line product problem")