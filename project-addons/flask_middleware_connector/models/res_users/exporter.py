# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ResUsersExporter(Component):
    _name = 'res.users.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['res.users']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"name": binding.name,
                "email": binding.email,
                "odoo_id": binding.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class CommercialAdapter(Component):

    _name = 'commercial.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'res.users'
    _middleware_model = 'commercial'
