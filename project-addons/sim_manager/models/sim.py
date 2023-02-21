from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json
import logging
from odoo.addons.queue_job.job import job
import requests
import urllib
from odoo.exceptions import UserError


logger = logging.getLogger(__name__)


class SimPackage(models.Model):
    _name = 'sim.package'
    _description = 'simPackage'
    _rec_name = 'code'
    _inherit = 'mail.thread'

    code = fields.Char(string='Package')
    serial_ids = fields.One2many('sim.serial', 'package_id', string='Cards')
    partner_id = fields.Many2one('res.partner', string='Sold to')
    move_id = fields.Many2one('stock.move')
    sale_id = fields.Many2one('sale.order', compute='_get_sale_order')
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

    @api.multi
    def write(self, vals):

        if 'partner_id' in vals:
            for package in self:
                new_partner_id = self.env['res.partner'].browse(vals['partner_id'])
                package.message_post(body=_(
                    "<ul><li> Officer: %s</il><li> Partner: %s <b>&rarr;</b> %s</il></ul>"
                ) % (self.env.user.partner_id.name, package.partner_id.name, new_partner_id.name))
        return super().write(vals)

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

    @api.multi
    def _get_sale_order(self):
        for pkg in self:
            pkg.sale_id = pkg.move_id.sale_line_id.order_id

    def create_sims_using_barcode(self, barcode):
        logger.info("Imported SIM %s" % barcode)
        max_cards = int(self.env['ir.config_parameter'].sudo().get_param('package.sim.card.max'))

        created_code = self
        if len(created_code.serial_ids) < max_cards:
            sim_serial = self.env['sim.serial'].create({'code': barcode, 'package_id': created_code.id})
            if sim_serial:
                message = _("{} created").format(sim_serial.code)
                self.env.user.notify_info(message=message)

            action = self.env.ref('sim_manager.action_sim_package_creator_scan')
            result = action.read()[0]

            if len(created_code.serial_ids) == max_cards:
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
            if 'EU' in created_code.code or 'VIP' in created_code.code:
                new_code = 'M2M_CARD_' + created_code.code.split('_')[-2] + '_' \
                           + str(int(created_code.code.split('_')[-1])+1).zfill(6)
            else:
                new_code = 'M2M_CARD_' + str(int(created_code.code.split('_')[-1]) + 1).zfill(6)
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

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    @api.multi
    def notify_sale_web(self, mode):
        web_endpoint = self.env['ir.config_parameter'].sudo().get_param('web.sim.endpoint')
        c_code = self.env['ir.config_parameter'].sudo().get_param('country_code')
        for package in self:
            data = {
                "origin": c_code.lower(),
                "odoo_id": package.partner_id.id or 0,
                "partner_name": package.partner_id.name or '',
                "mode": mode,
                "codes": [sim.code for sim in package.serial_ids],
                "sim_package": package.code
            }
            api_key = self.env['ir.config_parameter'].sudo().get_param('web.sim.endpoint.key')
            headers = {'x-api-key': api_key}
            response = requests.post(web_endpoint, headers=headers, data=json.dumps({"data": data}))


class SimSerial(models.Model):
    _name = 'sim.serial'
    _description = 'simSerial'
    _rec_name = 'code'

    code = fields.Char(string='Serial')
    package_id = fields.Many2one('sim.package', string='Package')
    state = fields.Selection(
        compute='_get_sim_state', string="State", readonly=True,
        selection=[
            ('active', 'Active'),
            ('active_disuse', 'Active disuse'),
            ('unsuscribed', 'Unsuscribed'),
            ('blocked', 'Blocked'),
            ('preactivated', 'Preactivated')
        ]
    )
    sim_service_ids = fields.One2many('sim.service', 'sim_serial_id', string="Services")

    def _get_sim_state(self):
        """
        Returns the state of the SimSerial from the web
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('web.sim.invoice.endpoint.key')
        headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
        data = {'iccid': self.code}
        web_endpoint = (
            f"{self.env['ir.config_parameter'].sudo().get_param('web.sim.detail.endpoint')}"
            f"?{urllib.parse.urlencode(data)}"
        )
        response = requests.get(web_endpoint, headers=headers, data=json.dumps({}))
        if response.status_code == 200:
            self.state = json.loads(response.content.decode('utf-8'))['state']
        else:
            raise UserError(_('Error while reading SIM state'))

    def _set_state_to_sim(self, new_state):
        """
        Given a new state, sets this state to the SIM Serial.
        """
        if self.sim_service_ids.filtered(lambda service: service.status == 'blocked'):
            raise UserError(_('Cannot block a SIM Service'))

        posible_states = ('active', 'active_disuse', 'unsuscribed', 'blocked', 'preactivated')
        if new_state not in posible_states:
            raise UserError(_('A SimSerial cannot have state %s') % new_state)

        api_key = self.env['ir.config_parameter'].sudo().get_param('web.sim.invoice.endpoint.key')
        headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
        body = {
            "iccid": self.code,
            "simServices": {f"{s['type']}Service": s['status'] for s in self.sim_service_ids},
            "state": new_state
        }
        web_endpoint = self.env['ir.config_parameter'].sudo().get_param('web.sim.update.endpoint')
        response = requests.put(web_endpoint, headers=headers, data=json.dumps(body))
        if response.status_code != 200:
            raise UserError(_("An error ocurred while updating the sim state"))

    def activate_sim(self):
        """
        Changes the state of the SIM to 'active'
        """
        self._set_state_to_sim('active')

    def deactivate_sim(self):
        """
        Changes the state of the SIM to 'unsuscribed'
        """
        self._set_state_to_sim('unsuscribed')

    def update_sim_services(self):
        """
        Synchronizes with web the services' states of the SimSerial
        """
        self._set_state_to_sim(self.state)

    def _get_sim_services(self):
        """
        Gets SIM details and creates the services of the SimSerial
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('web.sim.invoice.endpoint.key')
        headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
        data = {'iccid': self.code}
        web_endpoint = (
            f"{self.env['ir.config_parameter'].sudo().get_param('web.sim.detail.endpoint')}"
            f"?{urllib.parse.urlencode(data)}"
        )
        response = requests.get(web_endpoint, headers=headers, data=json.dumps({}))
        if response.status_code != 200:
            raise UserError(_('Error while getting SIM services'))
        services_response = json.loads(response.content.decode('utf-8'))['simServices']
        service_list = ('data', 'sms', 'voice')
        services_ids = [
            self.env['sim.service'].create({
                'sim_serial_id': self.id,
                'type': service_name,
                'status': services_response[f'{service_name}Service']
            }).id for service_name in service_list
        ]
        self.write({'sim_service_ids': [(6, 0, services_ids)]})

    @api.multi
    def action_open_sim_serial(self):
        """
        Returns the action that opens a SimSerial form
        """
        self._get_sim_services()
        action = self.env.ref('sim_manager.action_open_sim_serial').read()[0]
        action['res_id'] = self.id
        action['domain'] = [('id', 'in', self.sim_service_ids.ids)]
        return action


class SimType(models.Model):
    _name = 'sim.type'
    _description = 'simType'
    _rec_name = 'type'

    product_id = fields.Many2one('product.product')
    type = fields.Char('Type')
    code = fields.Char('Code')


class SimExport(models.TransientModel):
    _name = 'sim.export.wzd'

    mode = fields.Selection(
        string='Mode',
        selection=[('sold', 'Sold'),
                   ('return', 'Return'), ])

    def sync_sim_web(self):
        pkg = self.env['sim.package'].browse(self.env.context["active_ids"])
        pkg.with_delay(priority=10).notify_sale_web(self.mode)


class SimService(models.TransientModel):
    """
    Models the different services that a SimSerial has
    """
    _name = "sim.service"
    _description = "Sim Service"

    sim_serial_id = fields.Many2one('sim.serial', string="Code")
    type = fields.Selection(string="Type", selection=[
        ("data", "Data"), ("sms", "SMS"), ("voice", "Voice")
    ])
    status = fields.Selection(string="Status", selection=[
        ("activated", "Activated"), ("deactivated", "Deactivated"), ("blocked", "Blocked")
    ])
