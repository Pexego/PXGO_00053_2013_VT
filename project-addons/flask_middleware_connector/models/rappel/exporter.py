# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class RappelExporter(Component):
    _name = 'rappel.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['rappel']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"odoo_id": binding.id,
                "name": binding.name,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class RappelAdapter(Component):

    _name = 'rappel.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'rappel'
    _middleware_model = 'rappel'


class RappelInfoExporter(Component):
    _name = 'rappel.current.info.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['rappel.current.info']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"odoo_id": binding.id,
                "partner_id": binding.partner_id.id,
                "rappel_id": binding.rappel_id.id,
                "date_start": binding.date_start,
                "date_end": binding.date_end,
                "amount": binding.amount,
                "amount_est": binding.amount_est,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class RappelInfoAdapter(Component):

    _name = 'rappelcustomerinfo.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'rappel.current.info'
    _middleware_model = 'rappelcustomerinfo'


class RappelSectionExporter(Component):
    _name = 'rappel.section.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['rappel.section']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "odoo_id": binding.id,
            "rappel_id": binding.rappel_id.id,
            "percent": binding.percent,
            "rappel_from": binding.rappel_from,
            "rappel_until": binding.rappel_until,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class RappelSectionAdapter(Component):

    _name = 'rappelsection.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'rappel.section'
    _middleware_model = 'rappelsection'
