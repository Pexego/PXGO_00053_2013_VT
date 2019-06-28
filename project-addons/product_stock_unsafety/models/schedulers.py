# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, _, api, registry
from psycopg2 import OperationalError


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.multi
    def update_under_minimum(self, vals):
        """
        First check if already exists under_minimum in purchase state. If
        exists we do nothing. If not exist we check if exist under_minimum
        in progress state, if that case we update it else we create a new one
        """

        stock_unsafety = self.env['product.stock.unsafety']
        domain = [
            ('state', '=', 'in_action'),
            ('product_id', '=', vals['product_id'])
        ]
        under_mins = stock_unsafety.search(domain)
        if not under_mins:
            domain = [
                ('state', 'in', ['in_progress', 'exception']),
                ('product_id', '=', vals['product_id'])
            ]
            under_mins = stock_unsafety.search(domain)
            if under_mins:
                under_mins.write(vals)
            else:
                stock_unsafety.create(vals)
        return

    #TODO: Mograr, pero no se usa, analizar el motivo
    # ~ @api.model
    # ~ def _procure_orderpoint_confirm(
            # ~ self, use_new_cursor=False, company_id=False):
        # ~ '''
        # ~ Create procurement based on Orderpoint
        # ~ :param bool use_new_cursor: if set, use a dedicated cursor and
            # ~ auto-commit after processing each procurement.
            # ~ This is appropriate for batch jobs only.
         # ~ If the remaining days of product sales are less than the
         # ~ minimum selling days configured in the rule of minimum stock
         # ~ of the product. So instead of creating another provision that would
         # ~ create a purchase, ast would by default,
         # ~ creates a under minimum model.
        # ~ '''
        # ~ if use_new_cursor:
            # ~ cr = registry(self._cr.dbname).cursor()
            # ~ self = self.with_env(self.env(cr=cr))

        # ~ dom = company_id and [('company_id', '=', company_id)] or []
        # ~ orderpoints = self.env['stock.warehouse.orderpoint'].search(dom)
        # ~ while orderpoints:
            # ~ orderpoints_step = orderpoints[:100]
            # ~ del orderpoints[:100]
            # ~ for op in orderpoints_step:
                # ~ prod = op.product_id
                # ~ if not prod.active or prod.replacement_id:
                    # ~ continue
                # ~ domain = ['|', ('warehouse_id', '=', op.warehouse_id.id),
                          # ~ ('warehouse_id', '=', False),
                          # ~ ('location_id', '=', op.location_id.id)]
                # ~ product_route_ids = \
                    # ~ [x.id for x in
                     # ~ prod.route_ids + prod.categ_id.total_route_ids]
                # ~ rule = self.env['procurement.rule'].search(
                    # ~ domain + [('route_id', 'in', product_route_ids)],
                    # ~ order='route_sequence, sequence', limit=1)
                # ~ if rule:
                    # ~ seller = False
                    # ~ bom_id = False
                    # ~ delay = 0
                    # ~ if rule.action == 'manufacture':
                        # ~ product_type = 'manufacture'
                        # ~ bom_id = self.env['mrp.bom']._bom_find(
                            # ~ product=prod)
                        # ~ if not bom_id:
                            # ~ state = 'exception'
                        # ~ else:
                            # ~ state = 'in_progress'
                            # ~ delay = prod.produce_delay or 0
                            # ~ bom_id = bom_id
                    # ~ else:
                        # ~ product_type = 'buy'
                        # ~ if prod.seller_ids:
                            # ~ seller = prod.seller_ids[0]
                            # ~ state = 'in_progress'
                            # ~ delay = seller.delay or 0
                        # ~ else:
                            # ~ state = 'exception'
                # ~ else:
                    # ~ state = 'exception'

                # ~ days_sale = prod.remaining_days_sale
                # ~ min_days_sale = op.min_days_id.days_sale
                # ~ real_minimum = min_days_sale + delay
                # ~ if (days_sale < real_minimum):
                    # ~ vals = {'product_id': prod.id,
                            # ~ 'name': _('Minimum Stock Days'),
                            # ~ 'supplier_id': seller and seller.name.id or False,
                            # ~ 'orderpoint_id': op.id,
                            # ~ 'responsible': self.env.user.id,
                            # ~ 'state': state,
                            # ~ 'min_days_id': op.min_days_id.id,
                            # ~ 'bom_id': bom_id,
                            # ~ 'product_type': product_type,
                            # ~ 'brand_id': prod.product_brand_id.id}
                    # ~ daylysales = prod.get_daily_sales()
                    # ~ remaining_days = real_minimum - days_sale
                    # ~ if daylysales and remaining_days:
                        # ~ vals['minimum_proposal'] = \
                            # ~ round(daylysales * remaining_days)

                    # ~ # Creating or updating existing under minimum
                    # ~ self.update_under_minimum(vals)

        # ~ try:
            # ~ if use_new_cursor:
                # ~ self.env.cr.commit()
        # ~ except OperationalError:
            # ~ if use_new_cursor:
                # ~ self.env.cr.rollback()
                # ~ return
            # ~ else:
                # ~ raise

        # ~ if use_new_cursor:
            # ~ self.env.cr.commit()
            # ~ self.env.cr.close()
        # ~ return {}
