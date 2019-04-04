# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class CountryExporter(Component):
    _name = 'res.country.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['res.country']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"name": binding.name,
                "code": binding.code,
                "odoo_id": binding.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class CountryAdapter(Component):

    _name = 'country.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'res.country'
    _middleware_model = 'country'


class CountryStateExporter(Component):
    _name = 'res.country.state.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['res.country.state']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        backend_adapter = self.component(usage='backend.adapter')
        vals = {"name": binding.name,
                "code": binding.code,
                "country_id": binding.country_id.id,
                "odoo_id": binding.id}
        if mode == "insert":
            return backend_adapter.insert(vals)
        else:
            return backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        backend_adapter = self.component(usage='backend.adapter')
        return self.backend_adapter.remove(binding.id)


class CountryStateAdapter(Component):

    _name = 'country.state.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'res.country.state'
    _middleware_model = 'countrystate'
