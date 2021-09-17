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
            serials = [s.code for s in pkg.serial_ids]
            serials += [False for x in range(10-len(serials))]
            pkg.sim_1 = serials[0]
            pkg.sim_2 = serials[1]
            pkg.sim_3 = serials[2]
            pkg.sim_4 = serials[3]
            pkg.sim_5 = serials[4]
            pkg.sim_6 = serials[5]
            pkg.sim_7 = serials[6]
            pkg.sim_8 = serials[7]
            pkg.sim_9 = serials[8]
            pkg.sim_10 = serials[9]

    def create_sims_using_barcode(self, barcode):
        logger.info("Imported SIM %s" % barcode)
        max_cards = int(self.env['ir.config_parameter'].sudo().get_param('package.sim.card.max'))

        created_code = self.env['sim.package'].search([], order="create_date desc", limit=1)
        if len(created_code.serial_ids) < max_cards:
            sim_serial = self.env['sim.serial'].create({'code': barcode, 'package_id': created_code.id})
            if sim_serial:
                message = _("{} created").format(sim_serial.code)
                self.env.user.notify_info(message=message)

            action = self.env.ref('sim_manager.action_sim_package_creator_scan')
            result = action.read()[0]

            if len(created_code.serial_ids) == max_cards: #TODO: PARAMETRIZAR
                # We reach the maximum serials per package
                context = safe_eval(result['context'])
                context.update({
                    'default_state': 'warning',
                    'default_status': _('Package %s finished. Scan for continue with next package') % created_code.code,
                    'default_res_id': created_code.id,
                })
                result['context'] = json.dumps(context)
            else:
                context = safe_eval(result['context'])
                context.update({
                    'default_state': 'waiting',
                    'default_status': _('Scan the #%s serial for %s') % (len(created_code.serial_ids) + 1, created_code.code),
                    'default_res_id': created_code.id,
                })
                result['context'] = json.dumps(context)
        elif len(created_code.serial_ids) == max_cards:
            # Create the next package and return to scan all the codes
            new_code = 'M2M_CARD_' + created_code.code.split('_')[-2] + '_' \
                       + str(int(created_code.code.split('_')[-1])+1).zfill(6)
            pkg = self.env['sim.package'].create({'code': new_code})

            sim_serial = self.env['sim.serial'].create({'code': barcode, 'package_id': pkg.id})
            if sim_serial:
                message = _("{} created").format(sim_serial.code)
                self.env.user.notify_info(message=message)

            action = self.env.ref('sim_manager.action_sim_package_creator_scan')
            result = action.read()[0]

            context = safe_eval(result['context'])
            context.update({
                'default_state': 'waiting',
                'default_status': _('Scan the #%s serial for %s') % (len(pkg.serial_ids) + 1, pkg.code),
                'default_res_id': pkg.id,
            })
            result['context'] = json.dumps(context)

        return result


class SimSerial(models.Model):
    _name = 'sim.serial'
    _description = 'simSerial'

    code = fields.Char(string='Serial')
    package_id = fields.Many2one('sim.package', string='Package')
