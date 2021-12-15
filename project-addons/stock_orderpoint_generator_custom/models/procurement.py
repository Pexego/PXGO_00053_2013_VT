from odoo import models, api

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _procure_orderpoint_confirm(self, use_new_cursor=False, company_id=False):
        context = dict(self.env.context, remove_reserves=True)
        return super(ProcurementGroup, self.with_context(context))._procure_orderpoint_confirm(use_new_cursor,
                                                                                               company_id)

    @api.model
    def run(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        if self._context.get('remove_reserves', False):
            product_qty -= product_id.reservation_count
            if product_qty <= 0:
                return False
        return super(ProcurementGroup, self).run(product_id, product_qty, product_uom, location_id, name, origin,
                                                 values)
