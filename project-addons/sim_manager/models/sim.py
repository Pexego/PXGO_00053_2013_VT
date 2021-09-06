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

    def create_package_using_barcode(self, barcode):
        logger.info("Imported SIM %s" % barcode)
        barcode = barcode.replace("?", "_")
        next_serial = False
        next_serial_2 = False
        if 'M2M' in barcode:
            package = self.search([('code', '=', barcode)])
            if not package:
                sim_pkg = self.create({'code': barcode})
                if sim_pkg:
                    message = _("{} created").format(sim_pkg.code)
                    self.env.user.notify_info(message=message)
                    next_serial = True
            else:
                sim_pkg = package
                message = _("{} already exists").format(barcode)
                self.env.user.notify_warning(message=message)
                next_serial = True
        elif self.id > 0:
            # The barcode is a serial
            sim_serial = self.env['sim.serial'].create({'code': barcode, 'package_id': self.id})
            if sim_serial:
                message = _("{} created").format(sim_serial.code)
                self.env.user.notify_info(message=message)
                next_serial_2 = True

        action = self.env.ref('sim_manager.action_sim_package_creator')
        result = action.read()[0]

        if next_serial:
            context = safe_eval(result['context'])
            context.update({
                'default_state': 'warning',
                'default_status': _('Scan the serials for %s') % sim_pkg.code,
                'default_res_id': sim_pkg.id,
            })
            result['context'] = json.dumps(context)
        elif next_serial_2:
            context = safe_eval(result['context'])
            context.update({
                'default_state': 'warning',
                'default_status': _('Scan the serials for %s') % self.code,
                'default_res_id': self.id,
            })
            result['context'] = json.dumps(context)

        return result


class SimSerial(models.Model):
    _name = 'sim.serial'
    _description = 'simSerial'

    code = fields.Char(string='Serial')
    package_id = fields.Many2one('sim.package', string='Package')
