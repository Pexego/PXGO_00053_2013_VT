from openerp import models, fields, api, _, exceptions

CHECK_ERROR = {('0', 'Error Request'),
               ('1', 'Information Available'),
               ('-1', 'No Information')}


class PickingTrackingStatus(models.TransientModel):

    _name = "picking.tracking.status"
    _description = "Picking Tracking Status"

    @api.model
    def _default_status_picking(self):
        context = self.env.context
        if 'information' in context and context['information'].get('Package_status'):
            res = context['information'].get('Package_status').upper()
        else:
            res = False
        return res

    @api.model
    def _default_status_request(self):
        context = self.env.context
        if 'information' in context and context['information'].get('Bags'):
            info = context.get('information')
        else:
            return '-1'
        res = str(info["Status"])
        return res

    status_picking = fields.Char(string='STATUS', default=_default_status_picking, readonly=True)
    status_request = fields.Selection(CHECK_ERROR, string='Status request',
                                      default=_default_status_request, readonly=True)
    status_list = fields.One2many('picking.tracking.status.list', 'wizard_id', string='STATUS LIST', readonly=True)
    num_packages = fields.Integer(string='Num Packages', readonly=True)


class PickingTrackingStatus(models.TransientModel):

    _name = "picking.tracking.status.list"
    _description = "Picking Tracking Status List"

    wizard_id = fields.Many2one('picking.tracking.status')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    status = fields.Char(string="Status")
    city = fields.Char(string="City")
    date = fields.Char(string="Date")
    last_record = fields.Boolean()
    packages_reference = fields.Char(string="Tracking number")

