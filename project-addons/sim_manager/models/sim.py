from odoo import models, fields, _
from odoo.tools.safe_eval import safe_eval
import json
import logging

logger = logging.getLogger(__name__)


class SimPackage(models.Model):
    _name = 'sim.package'
    _description = 'simPackage'
    _rec_name = 'code'

    code = fields.Char(string='Package')
    serial_ids = fields.One2many('sim.serial', 'package_id', string='Cards')
    partner_id = fields.Many2one('res.partner', string='Sold to')
    move_id = fields.Many2one('stock.move')
    state = fields.Selection(string='State',
                             default='available',
                             selection=[('available', 'Available'),
                                        ('sold', 'Sold')])

    def create_sims_using_barcode(self, barcode):
        logger.info("Imported SIM %s" % barcode)

        created_code = self.env['sim.package'].search([], order="create_date desc", limit=1)
        sim_serial = self.env['sim.serial'].create({'code': barcode, 'package_id': created_code.id})
        if sim_serial:
            message = _("{} created").format(sim_serial.code)
            self.env.user.notify_info(message=message)

        action = self.env.ref('sim_manager.action_sim_package_creator_scan')
        result = action.read()[0]

        context = safe_eval(result['context'])
        context.update({
            'default_state': 'waiting',
            'default_status': _('Scan the serials for %s') % created_code.code,
            'default_res_id': created_code.id,
        })
        result['context'] = json.dumps(context)

        return result


class SimSerial(models.Model):
    _name = 'sim.serial'
    _description = 'simSerial'

    code = fields.Char(string='Serial')
    package_id = fields.Many2one('sim.package', string='Package')
