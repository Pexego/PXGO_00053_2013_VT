# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for sale in self:
            sale.picking_ids.write({'commercial': sale.user_id.id})
        return res
