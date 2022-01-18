from odoo import models, api

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _procure_orderpoint_confirm(self, use_new_cursor=False, company_id=False):
        context = dict(self.env.context, modify_stock_qty=True)
        return super(ProcurementGroup, self.with_context(context))._procure_orderpoint_confirm(use_new_cursor,
                                                                                               company_id)

