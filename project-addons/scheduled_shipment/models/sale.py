# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import models, fields, api, SUPERUSER_ID, exceptions, _
from openerp.exceptions import ValidationError
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.queue.job import job
    from openerp.addons.connector.session import ConnectorSession
except ImportError:
    _logger.debug('Can not `import connector`.')
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
                    raise ValidationError("Scheduled date must be bigger than current date")
        return super(SaleOrder, self).write(vals)


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    scheduled_picking = fields.Boolean(default="False")

    @api.multi
    def _process_picking_scheduled_time(self):
        """Process picking shipping in a scheduled date"""
        for picking in self:
            scheduled_date = datetime.strptime(picking.sale_id.scheduled_date, '%Y-%m-%d %H:%M:%S')
            session = ConnectorSession(self.env.cr, SUPERUSER_ID, context=self.env.context)
            make_picking_sync.delay(session, 'stock.picking', picking.id, eta=scheduled_date)


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _picking_assign(self, procurement_group, location_from, location_to):
        res = super(StockMove, self)._picking_assign(procurement_group, location_from, location_to)
        pickings = self.mapped('picking_id')
        for pick in pickings:
            if pick.sale_id.scheduled_date and not pick.not_sync:
                pick.not_sync = True
                pick.scheduled_picking = True
                pick._process_picking_scheduled_time()
        return res


@job(default_channel='root.schedule_picking')
def make_picking_sync(session, model_name, picking_id):
    model = session.env[model_name]
    picking = model.browse(picking_id)
    if picking.exists():
        list_picks = model.search([('origin', '=', picking.origin), ('state', '!=', 'cancel')])
        for pick in list_picks:
            pick.not_sync = False

