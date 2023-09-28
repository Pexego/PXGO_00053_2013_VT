from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    state = fields.Selection(selection_add=[('purchase_order', 'Purchase Order State')])

    partner_ref = fields.Char()

    order_id = fields.Many2one('purchase.order')

    def _select(self):
        return """
                , s.id AS order_id, s.partner_ref as partner_ref
                """

    def _group_by(self):
        return ", s.id, s.partner_ref"

    @api.model_cr
    def init(self):
        """Inject parts in the query with this hack, fetching the query and
        recreating it. Query is returned all in upper case and with final ';'.
        """
        super(PurchaseReport, self).init()
        self._cr.execute("SELECT pg_get_viewdef(%s, true)", (self._table,))
        view_def = self._cr.fetchone()[0]
        if view_def[-1] == ';':  # Remove trailing semicolon
            view_def = view_def[:-1]
        view_def = view_def.replace(
            "FROM purchase_order_line",
            f"{self._select()} FROM purchase_order_line",
        )
        view_def += self._group_by()
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"create or replace view {self._table} as ({view_def})")
