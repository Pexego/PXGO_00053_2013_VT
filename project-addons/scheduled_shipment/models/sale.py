# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields, api, SUPERUSER_ID, exceptions, _
from odoo.exceptions import ValidationError
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    scheduled_date = fields.Datetime('Scheduled Date')

    @api.multi
    def write(self, vals):
        # If order is in a finished state, don't check scheduled date
        if self.state not in ('progress', 'manual', 'shipping_except', 'invoice_except', 'done', 'history', 'cancel'):
            if 'scheduled_date' in vals:
                scheduled_date = vals['scheduled_date']
            else:
                scheduled_date = self.scheduled_date

            if scheduled_date:
                date_now = str(datetime.now())
                difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                    datetime.strptime(scheduled_date, '%Y-%m-%d %H:%M:%S')
                difference = difference.total_seconds() / float(60)
                if difference > 0:
                    raise ValidationError(_("Scheduled date must be bigger than current date"))
        return super(SaleOrder, self).write(vals)


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    scheduled_picking = fields.Boolean(default="False")
    scheduled_shipping_date = fields.Datetime('Scheduled shipping date', related='sale_id.scheduled_date', readonly=True)

    @api.multi
    def _process_picking_scheduled_time(self):
        """Process picking shipping in a scheduled date"""
        for picking in self:
            scheduled_date = datetime.strptime(picking.sale_id.scheduled_date, '%Y-%m-%d %H:%M:%S')
            picking.with_delay(eta=scheduled_date).make_picking_sync()

    @api.multi
    def action_shedule(self):

        view_id = self.env['stock.schedule.wizard']
        new = view_id.create({})

        return {
            'name': 'Schedule Shippement',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'stock.schedule.wizard',
            'src_model': 'stock.picking',
            'res_id': new.id,
            'type': 'ir.actions.act_window',
            'id': 'action_schedule_shipping_wizard',
            'context': {'parent_obj': self.id},
            }

    @job(default_channel='root.schedule_picking')
    @api.multi
    def make_picking_sync(self):
        if self.state != 'cancel':
            #self.not_sync = False
            pass


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _assign_picking(self):
        res = super(StockMove, self)._assign_picking()
        pickings = self.mapped('picking_id')
        for pick in pickings:
            if pick.sale_id.scheduled_date:  # TODO: descomentar al migrar crm_claim_rma_custom and not pick.not_sync:
               # pick.not_sync = True
                pick.scheduled_picking = True
                pick._process_picking_scheduled_time()
        return res

