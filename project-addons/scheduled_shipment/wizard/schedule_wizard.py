from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class StockScheduleWizard(models.TransientModel):

    _name = "stock.schedule.wizard"

    scheduled_date = fields.Datetime('Scheduled shipping date')

    @api.multi
    def action_button_schedule(self):
        if self.scheduled_date:
            date_now = str(datetime.now())
            difference = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S.%f') - \
                         datetime.strptime(self.scheduled_date, '%Y-%m-%d %H:%M:%S')
            difference = difference.total_seconds() / float(60)
            if difference > 0:
                raise ValidationError(_("Scheduled date must be bigger than current date"))

            picking = self.env['stock.picking'].browse(self.env.context['parent_obj'])
            self._clean_scheduled_crons(picking)

            picking.sale_id.scheduled_date = self.scheduled_date
            picking.not_sync = True
            picking._process_picking_scheduled_time()

    def _clean_scheduled_crons(self, picking):
        """
        Removes scheduled crons that synchronize picking

        Parameters:
        ----------
        picking:
            Picking to clean the crons of its synchronization
        """
        cron_ids = self.env['queue.job'].search([
            ('model_name', '=', 'stock.picking'), ('state', '=', 'pending'),
            ('record_ids', 'like', picking.id), ('method_name', '=', 'make_picking_sync')
        ])
        for cron in cron_ids:
            cron.unlink()
