from odoo import models, _, api, fields, exceptions
from odoo.addons.queue_job.job import job
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _compute_customizations(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                customization_ids = self.env['kitchen.customization']
                for move in picking.move_lines:
                    customization_line = move.customization_line
                    if customization_line:
                        customization_ids += customization_line.mapped('customization_id')
                picking.customization_ids = [(6, 0, customization_ids.ids)]
                picking.customization_count = len(set(customization_ids))

    customization_ids = fields.One2many('kitchen.customization', compute="_compute_customizations")

    customization_count = fields.Integer(compute='_compute_customizations', default=0)

    def action_view_customizations(self):
        if self.env.user.has_group('kitchen.group_kitchen'):
            action = self.env.ref('kitchen.action_show_customizations_kitchen').read()[0]
        else:
            action = self.env.ref('kitchen.action_show_customizations_commercials').read()[0]
        if len(self.customization_ids) > 0:
            action['domain'] = [('id', 'in', self.customization_ids.ids)]
            action['context'] = [('id', 'in', self.customization_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_cancel(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                customizations = picking.customization_ids.filtered(lambda c:c.state!='cancel')
                if customizations:
                    customizations_in_progress = customizations.filtered(lambda c1: c1.state in ('done', 'in_progress'))
                    if customizations_in_progress:
                        raise exceptions.UserError(
                            _("You cannot cancel this picking because there are customizations in progress"))
                    elif picking.sale_id:
                        return self.env['cancel.customizations.wiz'].create({
                            'picking_id': picking.id,
                            'origin_reference':
                                '%s,%s' % ('stock.picking', picking.id),
                            'continue_method': 'action_cancel',
                            'customizations_ids': [(6, 0, picking.customization_ids.ids)]
                        }).action_show()

        return super(StockPicking, self).action_cancel()

    @job(default_channel='root.schedule_picking')
    @api.multi
    def make_picking_sync(self):
        res = super(StockPicking, self).make_picking_sync()
        customization = self.customization_ids.filtered(lambda c: c.state != 'cancel')
        if customization:
            template = self.env.ref('kitchen.send_mail_to_kitchen_customization_scheduled_date')
            ctx = dict()
            ctx.update({
                'lang': 'es_ES'
            })
            template.with_context(ctx).send_mail(customization.id)
        return res

    @api.multi
    def action_accept_confirmed_qty(self):
        bcks = super(StockPicking, self).action_accept_confirmed_qty()
        for bck in bcks:
            pick = bck.backorder_id
            if bck.customization_ids and pick.customization_ids:
                bck.customization_ids.create_backorder_customization(bck.move_lines)
                bck.not_sync = True
                bck.message_post(
                    body=_('This picking has been created from an order with customized products'))
            elif bck.customization_ids:
                bck.not_sync = True
                if not ((pick.group_id and pick.group_id.sale_id and pick.group_id.sale_id.not_sync_picking)
                        or (pick.scheduled_shipping_date and datetime.strptime(pick.scheduled_shipping_date, '%Y-%m-%d %H:%M:%S') > datetime.now())):
                    pick.not_sync = False
        return bcks

    @api.multi
    def check_send_email_extended(self, vals):
        res = super(StockPicking, self).check_send_email_extended(vals)
        return res and (not self.customization_ids or not self.customization_ids.filtered(lambda c: c.state != 'cancel'))


class StockMove(models.Model):
    _inherit = 'stock.move'

    customization_line = fields.Many2one('kitchen.customization.line')
