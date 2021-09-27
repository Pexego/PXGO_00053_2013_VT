from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json


class SimPackageCreateWizard(models.TransientModel):

    _name = "sim.package.create.wizard"

    type_sim = fields.Many2one('sim.type', string='Type', required=True)

    new_code = fields.Char(string='New package', compute='_get_new_code', store=True)

    @api.depends('type_sim')
    def _get_new_code(self):
        if not self.type_sim:
            self.new_code = ''
        else:
            if self.type_sim.type == 'ES':
                last_code = self.env['sim.package'].search([('code', 'ilike', self.type_sim.code),
                                                            ('code', 'not like', 'EU'),
                                                            ('code', 'not like', 'VIP')], order="code desc", limit=1)
            else:
                last_code = self.env['sim.package'].search([('code', 'ilike', self.type_sim.code)],
                                                           order="code desc", limit=1)
            if last_code:
                self.new_code = self.type_sim.code + '_' + str(int(last_code.code.split('_')[-1])+1).zfill(6)
            else:
                self.new_code = self.type_sim.code + '_000001'

    def create_package(self):
        context = self._context.copy()
        context.pop('default_state', False)
        pkg = self.env['sim.package'].with_context(context).create({'code': self.new_code})

        action = self.env.ref('sim_manager.action_sim_package_creator_scan')
        result = action.read()[0]

        context = safe_eval(result['context'])
        context.update({
            'default_state': 'waiting',
            'default_status': _('Scan the #1 serial for %s') % pkg.code,
            'default_res_id': pkg.id,
        })
        result['context'] = json.dumps(context)

        return result
