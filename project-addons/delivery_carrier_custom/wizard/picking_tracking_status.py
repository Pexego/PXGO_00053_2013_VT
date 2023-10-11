from odoo import models, fields, api


class PickingTrackingStatus(models.TransientModel):

    _name = "picking.tracking.status.wizard"
    _description = "Picking Tracking Status"

    @api.model
    def _default_status_picking(self):
        context = self.env.context
        res = False
        if context.get('information', {}).get('Package_status'):
            res = context['information'].get('Package_status').upper()
        return res

    @api.model
    def _default_status_request(self):
        context = self.env.context
        res = '-1'
        if context.get('information', {}).get('Bags'):
            res = str(context.get('information').get('Status'))
        return res

    status_picking = fields.Char(string='STATUS', default=_default_status_picking, readonly=True)
    status_request = fields.Selection([('0', 'Error Request'), ('1', 'Information Available'),
                                      ('-1', 'No Information')], string='Status request',
                                      default=_default_status_request, readonly=True)
    status_list = fields.One2many('picking.tracking.status.list.wizard', 'wizard_id', string='STATUS LIST', readonly=True)
    num_packages = fields.Integer(string='Num Packages', readonly=True)


class PickingTrackingStatusList(models.TransientModel):

    _name = "picking.tracking.status.list.wizard"
    _description = "Picking Tracking Status List"

    wizard_id = fields.Many2one('picking.tracking.status.wizard')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    status = fields.Char(string="Status")
    city = fields.Char(string="City")
    date = fields.Char(string="Date")
    last_record = fields.Boolean()
    packages_reference = fields.Char(string="Tracking number")
