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

    scheduled_date = fields.Datetime('Scheduled shipping date')
    not_sync_picking = fields.Boolean()

    @api.multi
    def write(self, vals):
        # If order is in a finished state, don't check scheduled date
        for sale in self:
            if sale.state not in ('sale','done', 'history',
                                  'cancel'):
                if 'scheduled_date' in vals:
                    scheduled_date = vals['scheduled_date']
                else:
                    scheduled_date = sale.scheduled_date

                if scheduled_date:
                    date_now = str(datetime.now())
                    difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                        datetime.strptime(scheduled_date, '%Y-%m-%d %H:%M:%S')
                    difference = difference.total_seconds() / float(60)
                    if difference > 0:
                        raise ValidationError(_("Scheduled date must be bigger than current date"))
        return super().write(vals)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.not_sync_picking:
            for picking in self.picking_ids:
                picking.not_sync = True
        return res

    @api.multi
    def copy(self, default=None):
        default = default or {}
        default['scheduled_date'] = False
        return super().copy(default)


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
            self.not_sync = False

    @api.multi
    def action_accept_confirmed_qty(self):
        bcks = super(StockPicking, self).action_accept_confirmed_qty()
        for bck in bcks:
            if bck.backorder_id.sale_id.scheduled_date:
                bck.not_sync = True
                bck.scheduled_picking = True
                bck._process_picking_scheduled_time()
        return bcks


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _assign_picking(self):
        res = super(StockMove, self)._assign_picking()
        pickings = self.mapped('picking_id')
        for pick in pickings:
            if pick.sale_id.scheduled_date and not pick.not_sync:
                pick.not_sync = True
                pick.scheduled_picking = True
                pick._process_picking_scheduled_time()
        return res
