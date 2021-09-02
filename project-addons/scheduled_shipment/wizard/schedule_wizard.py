from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class StockScheduleWizard(models.TransientModel):

    _name = "stock.schedule.wizard"

    scheduled_date = fields.Datetime('Scheduled shipping date')
    picking_id = fields.Many2one('stock.picking')

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
            old_scheduled_picking = self.env['stock.schedule.wizard'].search([('picking_id','=',picking.id)])

            if old_scheduled_picking:
                old_scheduled_picking = old_scheduled_picking[0]

                if self.scheduled_date > old_scheduled_picking.scheduled_date:
                    cron_id = self.env['queue.job'].search([('model_name','=','stock.picking'),('state','=','pending'),('record_ids','like',picking.id), ('method_name','=','make_picking_sync')])
                    cron_id.unlink()
                    

            self.picking_id = picking.id

            picking.sale_id.scheduled_date = self.scheduled_date
            picking.not_sync = True
            picking._process_picking_scheduled_time()
