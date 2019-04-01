# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ClaimExporter(Component):
    _name = 'crm.claim.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['crm.claim']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"odoo_id": binding.id,
                "date": binding.date,
                "date_received": binding.date_received,
                "delivery_type": binding.delivery_type,
                "stage_id": binding.stage_id.id,
                "partner_id": binding.partner_id.id,
                "number": binding.number,
                "last_update_date": binding.write_date,
                "delivery_address": binding.delivery_address_id.street,
                "delivery_zip": binding.delivery_address_id.zip,
                "delivery_city": binding.delivery_address_id.city,
                "delivery_state": binding.delivery_address_id.state_id.name,
                "delivery_country": binding.delivery_address_id.country_id.name,
                "type": binding.name}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ClaimAdapter(Component):

    _name = 'rma.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'crm.claim'
    _middleware_model = 'rma'


class ClaimLineExporter(Component):
    _name = 'claim.line.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['claim.line']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "odoo_id": binding.id,
            "id_rma": binding.claim_id.id,
            "reference": binding.claim_id.number,
            "name": binding.name,
            "move_out_customer_state": binding.move_out_customer_state,
            "internal_description": binding.internal_description and
            binding.internal_description.replace("\n", " ") or '',
            "product_returned_quantity": binding.product_returned_quantity,
            "product_id": binding.product_id.id,
            "equivalent_product_id": binding.equivalent_product_id.id,
            "entrance_date": binding.date_in,
            "end_date": binding.date_out,
            "status_id": binding.substate_id.id,
            "prodlot_id": binding.prodlot_id.name,
            "invoice_id": binding.invoice_id.number,
        }

        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ClaimLineAdapter(Component):

    _name = 'rmaproduct.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'claim.line'
    _middleware_model = 'rmaproduct'


class RmaStatusExporter(Component):
    _name = 'substate.substate.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['substate.substate']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "odoo_id": binding.id,
            "name": binding.name
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class RmaStatusAdapter(Component):

    _name = 'rmastatus.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'substate.substate'
    _middleware_model = 'rmastatus'



class RmaStageExporter(Component):
    _name = 'crm.claim.stage.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['crm.claim.stage']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "odoo_id": binding.id,
            "name": binding.name
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class RmaStageAdapter(Component):

    _name = 'rmastage.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'crm.claim.stage'
    _middleware_model = 'rmastage'
