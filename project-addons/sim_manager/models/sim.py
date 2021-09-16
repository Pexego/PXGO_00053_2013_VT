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

    # Report Fields
    sim_1 = fields.Char(string="Serie Inicio", compute='_get_serials')
    sim_2 = fields.Char(string="Serie 2", compute='_get_serials')
    sim_3 = fields.Char(string="Serie 3", compute='_get_serials')
    sim_4 = fields.Char(string="Serie 4", compute='_get_serials')
    sim_5 = fields.Char(string="Serie 5", compute='_get_serials')
    sim_6 = fields.Char(string="Serie 6", compute='_get_serials')
    sim_7 = fields.Char(string="Serie 7", compute='_get_serials')
    sim_8 = fields.Char(string="Serie 8", compute='_get_serials')
    sim_9 = fields.Char(string="Serie 9", compute='_get_serials')
    sim_10 = fields.Char(string="Serie Fin", compute='_get_serials')
    qty = fields.Char(string="Cantidad", default='10')

    def _get_serials(self):
        for pkg in self:
            pkg.sim_1 = pkg.serial_ids[0].code
            pkg.sim_2 = pkg.serial_ids[1].code
            pkg.sim_3 = pkg.serial_ids[2].code
            pkg.sim_4 = pkg.serial_ids[3].code
            pkg.sim_5 = pkg.serial_ids[4].code
            pkg.sim_6 = pkg.serial_ids[5].code
            pkg.sim_7 = pkg.serial_ids[6].code
            pkg.sim_8 = pkg.serial_ids[7].code
            pkg.sim_9 = pkg.serial_ids[8].code
            pkg.sim_10 = pkg.serial_ids[9].code


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
